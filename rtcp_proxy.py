"""Keep an Arlo camera's RTSP stream alive for FFmpeg-based clients.

Arlo Pro / Pro 2 cameras re-auth to Wi-Fi (killing the stream after ~6s) if they
stop receiving RTCP Receiver Reports. FFmpeg does not send them often enough.
This proxy owns the RTSP/UDP session with the camera itself, sends Receiver
Reports on a steady cadence (see arlo.rtcp), and relays the raw RTP to a local
UDP port that any FFmpeg-based consumer can read via a tiny SDP file.

    python3 rtcp_proxy.py rtsp://192.168.1.194/live --relay 127.0.0.1:5600

Then point FFmpeg at an SDP describing the relayed stream, e.g.:

    ffmpeg -protocol_whitelist file,udp,rtp -i stream.sdp ...

This module has no third-party dependencies. The live RTSP handshake needs a
real camera to validate end to end; the parsing helpers below are unit tested.
"""

import argparse
import re
import select
import socket
import sys
import time
from urllib.parse import urlparse

from arlo.rtcp import RtcpSession

USER_AGENT = "arlo-cam-api-rtcp-proxy"


def parse_control_url(base_url, sdp):
    """Resolve the track control URL from an SDP body against the stream URL."""
    control = None
    for line in sdp.splitlines():
        line = line.strip()
        if line.startswith("a=control:"):
            control = line[len("a=control:"):].strip()
            # prefer a media-level control line over the session-level one
            if control not in ("", "*"):
                break
    if not control or control == "*":
        return base_url
    if control.lower().startswith("rtsp://"):
        return control
    return base_url.rstrip("/") + "/" + control.lstrip("/")


def parse_server_port(transport):
    """Return (rtp_port, rtcp_port) from an RTSP Transport header, or None."""
    m = re.search(r"server_port=(\d+)(?:-(\d+))?", transport or "")
    if not m:
        return None
    rtp = int(m.group(1))
    rtcp = int(m.group(2)) if m.group(2) else rtp + 1
    return rtp, rtcp


def parse_session_id(session_header):
    """Return the session id from an RTSP Session header (dropping ;timeout=...)."""
    if not session_header:
        return None
    return session_header.split(";")[0].strip()


class RtspProxy:
    def __init__(self, camera_url, relay_host="127.0.0.1", relay_port=5600,
                 rr_period=1.0, local_rtp_port=5700):
        self.camera_url = camera_url
        parsed = urlparse(camera_url)
        self.camera_host = parsed.hostname
        self.camera_port = parsed.port or 554
        self.relay_addr = (relay_host, relay_port)
        self.rr_period = rr_period
        self.local_rtp_port = local_rtp_port

        self._cseq = 0
        self._ctrl = None          # TCP control socket to the camera
        self._session_id = None
        self._session = RtcpSession()
        self._running = False

    # -- RTSP control ---------------------------------------------------------

    def _send_request(self, method, url, headers=None):
        self._cseq += 1
        lines = [f"{method} {url} RTSP/1.0", f"CSeq: {self._cseq}", f"User-Agent: {USER_AGENT}"]
        if self._session_id:
            lines.append(f"Session: {self._session_id}")
        for k, v in (headers or {}).items():
            lines.append(f"{k}: {v}")
        request = "\r\n".join(lines) + "\r\n\r\n"
        self._ctrl.sendall(request.encode())
        return self._read_response()

    def _read_response(self):
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self._ctrl.recv(4096)
            if not chunk:
                raise RuntimeError("RTSP control connection closed")
            data += chunk
        head, _, rest = data.partition(b"\r\n\r\n")
        headers = {}
        for line in head.decode(errors="replace").split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        body = rest
        length = int(headers.get("content-length", 0))
        while len(body) < length:
            body += self._ctrl.recv(4096)
        return headers, body.decode(errors="replace")

    # -- lifecycle ------------------------------------------------------------

    def run(self):
        self._ctrl = socket.create_connection((self.camera_host, self.camera_port), timeout=10)
        try:
            self._send_request("OPTIONS", self.camera_url)
            _, sdp = self._send_request(
                "DESCRIBE", self.camera_url, {"Accept": "application/sdp"})
            track_url = parse_control_url(self.camera_url, sdp)

            rtp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtcp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtp_sock.bind(("", self.local_rtp_port))
            rtcp_sock.bind(("", self.local_rtp_port + 1))

            headers, _ = self._send_request("SETUP", track_url, {
                "Transport": f"RTP/AVP;unicast;client_port={self.local_rtp_port}-{self.local_rtp_port + 1}"})
            self._session_id = parse_session_id(headers.get("session"))
            server_ports = parse_server_port(headers.get("transport"))
            rtcp_server_addr = None
            if server_ports:
                rtcp_server_addr = (self.camera_host, server_ports[1])
                # punch a hole so the camera can reach our RTCP socket
                rtcp_sock.sendto(b"\x00", rtcp_server_addr)

            self._send_request("PLAY", self.camera_url, {"Range": "npt=0.000-"})
            relay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._running = True
            self._pump(rtp_sock, rtcp_sock, relay, rtcp_server_addr)
        finally:
            self.teardown()

    def _pump(self, rtp_sock, rtcp_sock, relay, rtcp_server_addr):
        next_rr = time.monotonic() + self.rr_period
        while self._running:
            timeout = max(0.0, next_rr - time.monotonic())
            readable, _, _ = select.select([rtp_sock, rtcp_sock], [], [], timeout)
            for sock in readable:
                data, _ = sock.recvfrom(65535)
                if sock is rtp_sock:
                    self._session.on_rtp(data)
                    relay.sendto(data, self.relay_addr)
                else:
                    self._session.on_sender_report(data)
                    self._send_rr(rtcp_sock, rtcp_server_addr)
            if time.monotonic() >= next_rr:
                self._send_rr(rtcp_sock, rtcp_server_addr)
                next_rr = time.monotonic() + self.rr_period

    def _send_rr(self, rtcp_sock, rtcp_server_addr):
        if not rtcp_server_addr:
            return
        report = self._session.build_receiver_report()
        if report:
            rtcp_sock.sendto(report, rtcp_server_addr)

    def teardown(self):
        self._running = False
        if self._ctrl:
            try:
                self._send_request("TEARDOWN", self.camera_url)
            except Exception:
                pass
            try:
                self._ctrl.close()
            except Exception:
                pass
            self._ctrl = None


def main(argv=None):
    parser = argparse.ArgumentParser(description="RTCP keepalive proxy for Arlo cameras")
    parser.add_argument("camera_url", help="camera RTSP URL, e.g. rtsp://192.168.1.194/live")
    parser.add_argument("--relay", default="127.0.0.1:5600",
                        help="host:port to relay RTP to (default 127.0.0.1:5600)")
    parser.add_argument("--rr-period", type=float, default=1.0,
                        help="seconds between Receiver Reports (default 1.0)")
    parser.add_argument("--local-rtp-port", type=int, default=5700,
                        help="local UDP port to receive RTP on (default 5700)")
    args = parser.parse_args(argv)

    relay_host, _, relay_port = args.relay.rpartition(":")
    proxy = RtspProxy(args.camera_url, relay_host or "127.0.0.1", int(relay_port),
                      rr_period=args.rr_period, local_rtp_port=args.local_rtp_port)
    print(f"Proxying {args.camera_url} -> {args.relay}, Receiver Reports every {args.rr_period}s")
    try:
        proxy.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"proxy error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
