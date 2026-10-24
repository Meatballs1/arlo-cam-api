import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arlo.rtcp import (
    RtcpSession,
    parse_rtp_header,
    parse_sender_reports,
)


def make_rtp(seq, ssrc, payload_type=96, timestamp=0):
    return struct.pack(">BBHII", 0x80, payload_type, seq, timestamp, ssrc) + b"payload"


def make_sr(ssrc, ntp, rtp_ts=0, packet_count=0, octet_count=0):
    # header(4) + sender ssrc(4) + sender info(20) = 28 bytes = 7 words -> length word = 6
    header = struct.pack(">BBH", 0x80, 200, 6)
    return header + struct.pack(">I", ssrc) + struct.pack(">QIII", ntp, rtp_ts, packet_count, octet_count)


def make_rr(ssrc):
    # a minimal (report-count 0) receiver report, used to test compound skipping
    return struct.pack(">BBH", 0x80, 201, 1) + struct.pack(">I", ssrc)


class TestRtpParsing(unittest.TestCase):
    def test_parse_rtp_header(self):
        pkt = make_rtp(seq=1234, ssrc=0xDEADBEEF)
        self.assertEqual(parse_rtp_header(pkt), (0xDEADBEEF, 1234))

    def test_parse_rtp_too_short(self):
        self.assertIsNone(parse_rtp_header(b"\x80\x60\x00"))

    def test_parse_rtp_wrong_version(self):
        pkt = bytearray(make_rtp(seq=1, ssrc=1))
        pkt[0] = 0x40  # version 1
        self.assertIsNone(parse_rtp_header(bytes(pkt)))


class TestSenderReportParsing(unittest.TestCase):
    def test_parse_single_sr(self):
        reports = parse_sender_reports(make_sr(ssrc=0x11223344, ntp=0x0102030405060708))
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].ssrc, 0x11223344)
        self.assertEqual(reports[0].ntp_timestamp, 0x0102030405060708)

    def test_parse_compound_skips_non_sr(self):
        packet = make_sr(ssrc=0xAABBCCDD, ntp=42) + make_rr(ssrc=0x99)
        reports = parse_sender_reports(packet)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].ssrc, 0xAABBCCDD)

    def test_parse_truncated_returns_empty(self):
        self.assertEqual(parse_sender_reports(b"\x80\xc8\x00"), [])


class TestReceiverReport(unittest.TestCase):
    def test_none_before_any_rtp(self):
        self.assertIsNone(RtcpSession().build_receiver_report())

    def test_report_structure(self):
        session = RtcpSession(local_ssrc=0x01020304)
        session.on_rtp(make_rtp(seq=1000, ssrc=0xCAFEBABE))
        session.on_rtp(make_rtp(seq=1001, ssrc=0xCAFEBABE))
        rr = session.build_receiver_report()

        self.assertEqual(len(rr), 32)
        b0, pt, length = struct.unpack_from(">BBH", rr, 0)
        self.assertEqual(b0 >> 6, 2)          # version 2
        self.assertEqual(b0 & 0x1F, 1)        # report count 1
        self.assertEqual(pt, 201)             # RR
        self.assertEqual(length, 7)           # 8 words - 1
        sender_ssrc = struct.unpack_from(">I", rr, 4)[0]
        self.assertEqual(sender_ssrc, 0x01020304)
        src_ssrc, lost, ext_seq, jitter, lsr, dlsr = struct.unpack_from(">IIIIII", rr, 8)
        self.assertEqual(src_ssrc, 0xCAFEBABE)
        self.assertEqual(lost, 0)
        self.assertEqual(ext_seq, 1001)
        self.assertEqual(lsr, 0)              # no SR seen yet
        self.assertEqual(dlsr, 0)

    def test_lsr_and_dlsr_after_sender_report(self):
        clock = {"t": 100.0}
        session = RtcpSession(local_ssrc=1, monotonic=lambda: clock["t"])
        session.on_rtp(make_rtp(seq=5, ssrc=0x22))
        session.on_rtp(make_rtp(seq=6, ssrc=0x22))

        ntp = 0xAABBCCDD11223344
        session.on_sender_report(make_sr(ssrc=0x22, ntp=ntp))  # recorded at t=100.0
        clock["t"] = 100.5                                      # 0.5s later
        rr = session.build_receiver_report()

        _, _, _, _, lsr, dlsr = struct.unpack_from(">IIIIII", rr, 8)
        self.assertEqual(lsr, (ntp >> 16) & 0xFFFFFFFF)         # middle 32 bits
        self.assertEqual(dlsr, int(0.5 * 65536))                # 1/65536s units

    def test_sender_report_from_other_source_ignored(self):
        session = RtcpSession(local_ssrc=1)
        session.on_rtp(make_rtp(seq=1, ssrc=0x1111))
        session.on_rtp(make_rtp(seq=2, ssrc=0x1111))
        session.on_sender_report(make_sr(ssrc=0x9999, ntp=123))  # different SSRC
        _, _, _, _, lsr, dlsr = struct.unpack_from(">IIIIII", session.build_receiver_report(), 8)
        self.assertEqual((lsr, dlsr), (0, 0))


class TestSequenceTracking(unittest.TestCase):
    def test_in_order(self):
        session = RtcpSession()
        for seq in (100, 101, 102, 103):
            session.on_rtp(make_rtp(seq=seq, ssrc=0x7))
        self.assertEqual(session.extended_highest_seq, 103)

    def test_sequence_wrap_increments_cycle(self):
        session = RtcpSession()
        for seq in (65534, 65535, 0):
            session.on_rtp(make_rtp(seq=seq, ssrc=0x7))
        self.assertEqual(session.extended_highest_seq, 65536)


if __name__ == "__main__":
    unittest.main()
