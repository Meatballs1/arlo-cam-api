"""RTP/RTCP helpers for keeping Arlo cameras streaming.

Arlo Pro / Pro 2 cameras drop their Wi-Fi association and force a re-auth if
they stop receiving RTCP Receiver Reports from the streaming client. FFmpeg
(and anything built on it) does not emit Receiver Reports often enough, so the
camera tears the stream down after a few seconds - the "FFmpeg kills the camera
after ~6 seconds" problem described in the README.

This module implements just enough of RFC 3550 to track an incoming RTP stream
and build well-formed Receiver Reports that keep the camera happy. It is pure
Python with no third-party dependencies, so it can be dropped into any pipeline.

The sequence-number tracking is a port of the reference algorithm in RFC 3550
Appendix A.1.
"""

import random
import struct
import time

RTP_SEQ_MOD = 1 << 16
MAX_DROPOUT = 3000
MAX_MISORDER = 100
MIN_SEQUENTIAL = 2

RTCP_PT_SR = 200
RTCP_PT_RR = 201


def parse_rtp_header(packet):
    """Return (ssrc, sequence_number) from an RTP packet, or None if malformed."""
    if len(packet) < 12:
        return None
    if (packet[0] >> 6) != 2:  # RTP version must be 2
        return None
    seq = struct.unpack_from(">H", packet, 2)[0]
    ssrc = struct.unpack_from(">I", packet, 8)[0]
    return ssrc, seq


class SenderReport:
    __slots__ = ("ssrc", "ntp_timestamp")

    def __init__(self, ssrc, ntp_timestamp):
        self.ssrc = ssrc
        self.ntp_timestamp = ntp_timestamp


def parse_sender_reports(packet):
    """Parse RTCP Sender Reports (PT=200) out of a (possibly compound) packet.

    Returns a list of SenderReport; non-SR packets in the compound are skipped.
    """
    reports = []
    offset = 0
    n = len(packet)
    while offset + 4 <= n:
        if (packet[offset] >> 6) != 2:  # version
            break
        pt = packet[offset + 1]
        length_words = struct.unpack_from(">H", packet, offset + 2)[0]
        pkt_len = (length_words + 1) * 4
        if pkt_len <= 0 or offset + pkt_len > n:
            break
        if pt == RTCP_PT_SR and pkt_len >= 28:
            ssrc = struct.unpack_from(">I", packet, offset + 4)[0]
            ntp = struct.unpack_from(">Q", packet, offset + 8)[0]
            reports.append(SenderReport(ssrc, ntp))
        offset += pkt_len
    return reports


class RtcpSession:
    """Tracks one incoming RTP stream and builds RTCP Receiver Reports for it."""

    def __init__(self, local_ssrc=None, monotonic=time.monotonic):
        self.source_ssrc = None
        self.local_ssrc = local_ssrc if local_ssrc is not None else random.getrandbits(32)
        self._monotonic = monotonic

        self._base_seq = 0
        self._max_seq = 0
        self._bad_seq = RTP_SEQ_MOD + 1
        self._cycles = 0
        self._received = 0
        self._probation = 0

        self._last_sr_ntp = None
        self._last_sr_monotonic = 0.0

    # -- RFC 3550 Appendix A.1 ------------------------------------------------

    def _init_seq(self, seq):
        self._base_seq = seq
        self._max_seq = seq
        self._bad_seq = RTP_SEQ_MOD + 1  # so seq == bad_seq is false
        self._cycles = 0
        self._received = 0

    def _update_seq(self, seq):
        udelta = (seq - self._max_seq) & 0xFFFF

        if self._probation:
            # Source not valid until MIN_SEQUENTIAL packets arrive in sequence.
            if seq == (self._max_seq + 1) & 0xFFFF:
                self._probation -= 1
                self._max_seq = seq
                if self._probation == 0:
                    self._init_seq(seq)
                    self._received += 1
                    return True
            else:
                self._probation = MIN_SEQUENTIAL - 1
                self._max_seq = seq
            return False
        elif udelta < MAX_DROPOUT:
            # In order, within permissible gap.
            if seq < self._max_seq:
                self._cycles += RTP_SEQ_MOD  # sequence number wrapped
            self._max_seq = seq
        elif udelta <= RTP_SEQ_MOD - MAX_MISORDER:
            # Very large jump in sequence number.
            if seq == self._bad_seq:
                # Two sequential packets - the sender likely restarted; re-sync.
                self._init_seq(seq)
            else:
                self._bad_seq = (seq + 1) & (RTP_SEQ_MOD - 1)
                return False
        else:
            # Duplicate or reordered packet.
            pass
        self._received += 1
        return True

    # -- public API -----------------------------------------------------------

    def on_rtp(self, packet):
        """Feed a received RTP packet so sequence stats stay current."""
        parsed = parse_rtp_header(packet)
        if parsed is None:
            return
        ssrc, seq = parsed
        if self.source_ssrc is None:
            self.source_ssrc = ssrc
            self._init_seq(seq)
            self._max_seq = (seq - 1) & 0xFFFF
            self._probation = MIN_SEQUENTIAL
        self._update_seq(seq)

    def on_sender_report(self, packet):
        """Feed a received RTCP packet; records the latest Sender Report."""
        for sr in parse_sender_reports(packet):
            if self.source_ssrc is None or sr.ssrc == self.source_ssrc:
                self._last_sr_ntp = sr.ntp_timestamp
                self._last_sr_monotonic = self._monotonic()

    @property
    def extended_highest_seq(self):
        return (self._cycles + self._max_seq) & 0xFFFFFFFF

    def build_receiver_report(self):
        """Return the bytes of an RTCP Receiver Report, or None if not ready.

        None is returned until at least one RTP packet has been seen (we have no
        source SSRC to report on yet). LSR/DLSR are zero until a Sender Report
        has been received, as specified by RFC 3550 section 6.4.2.
        """
        if self.source_ssrc is None:
            return None

        fraction_lost = 0
        cumulative_lost = 0
        jitter = 0

        if self._last_sr_ntp is not None:
            # LSR: middle 32 bits of the NTP timestamp from the most recent SR.
            lsr = (self._last_sr_ntp >> 16) & 0xFFFFFFFF
            # DLSR: delay since that SR, in units of 1/65536 seconds.
            delay = self._monotonic() - self._last_sr_monotonic
            dlsr = int(delay * 65536) & 0xFFFFFFFF
        else:
            lsr = 0
            dlsr = 0

        header = struct.pack(">BBH", 0x80 | 1, RTCP_PT_RR, 7)  # V=2, RC=1, len=7 words
        sender = struct.pack(">I", self.local_ssrc)
        block = struct.pack(
            ">IIIIII",
            self.source_ssrc,
            ((fraction_lost & 0xFF) << 24) | (cumulative_lost & 0xFFFFFF),
            self.extended_highest_seq,
            jitter,
            lsr,
            dlsr,
        )
        return header + sender + block
