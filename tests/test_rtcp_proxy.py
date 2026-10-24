import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rtcp_proxy import parse_control_url, parse_server_port, parse_session_id

BASE = "rtsp://192.168.1.194/live"


class TestControlUrl(unittest.TestCase):
    def test_relative_control(self):
        sdp = "v=0\r\nm=video 0 RTP/AVP 96\r\na=control:trackID=1\r\n"
        self.assertEqual(parse_control_url(BASE, sdp), "rtsp://192.168.1.194/live/trackID=1")

    def test_absolute_control(self):
        sdp = "m=video 0 RTP/AVP 96\r\na=control:rtsp://192.168.1.194/live/stream1\r\n"
        self.assertEqual(parse_control_url(BASE, sdp), "rtsp://192.168.1.194/live/stream1")

    def test_session_star_falls_back_to_base(self):
        sdp = "v=0\r\na=control:*\r\n"
        self.assertEqual(parse_control_url(BASE, sdp), BASE)

    def test_prefers_media_control_over_session_star(self):
        sdp = "v=0\r\na=control:*\r\nm=video 0 RTP/AVP 96\r\na=control:trackID=0\r\n"
        self.assertEqual(parse_control_url(BASE, sdp), "rtsp://192.168.1.194/live/trackID=0")


class TestServerPort(unittest.TestCase):
    def test_range(self):
        self.assertEqual(
            parse_server_port("RTP/AVP;unicast;client_port=5700-5701;server_port=6000-6001"),
            (6000, 6001))

    def test_single_port_implies_next(self):
        self.assertEqual(parse_server_port("RTP/AVP;unicast;server_port=6000"), (6000, 6001))

    def test_missing(self):
        self.assertIsNone(parse_server_port("RTP/AVP;unicast;client_port=5700-5701"))
        self.assertIsNone(parse_server_port(None))


class TestSessionId(unittest.TestCase):
    def test_with_timeout(self):
        self.assertEqual(parse_session_id("12345678;timeout=60"), "12345678")

    def test_plain(self):
        self.assertEqual(parse_session_id("ABCDEF"), "ABCDEF")

    def test_none(self):
        self.assertIsNone(parse_session_id(None))


if __name__ == "__main__":
    unittest.main()
