"""Deterministic gzip checks for host-specific Python 3.11/3.13 mismatch."""
import gzip
import hashlib
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from v6_wifi_patch import stable_gzip

class TestCanonicalGzip(unittest.TestCase):
    def test_known_header_and_round_trip(self):
        raw = b'LAKI V6 WIFI BT AUDIO' * 20000
        compressed = stable_gzip(raw)
        self.assertEqual(compressed[:10], bytes.fromhex('1f8b08000000000002ff'))
        self.assertEqual(gzip.decompress(compressed),raw)

    def test_repeated_result_is_byte_identical(self):
        raw=bytes(range(256))*800
        self.assertEqual(stable_gzip(raw),stable_gzip(raw))

    def test_header_differs_from_unix_os_variant_but_payload_is_same(self):
        canonical=stable_gzip(b'ANDROID' * 9000)
        unix=bytearray(canonical)
        unix[9]=3  # Python 3.11 gzip.compress(mtime=0) may emit this.
        self.assertEqual(gzip.decompress(canonical),gzip.decompress(bytes(unix)))
        self.assertNotEqual(hashlib.sha256(canonical).digest(),hashlib.sha256(unix).digest())

if __name__=='__main__': unittest.main()
