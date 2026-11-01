"""Tests for deliberate V6 Android identity. No proprietary blobs needed."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import patch_android_properties_v6 as ident

ORIG=(
 b'# original donor\nro.product.model=N5MAX\nro.product.brand=Amlogic\n'
 b'ro.product.name=N5MAX\nro.product.device=N5MAX\n'
 b'ro.product.manufacturer=Amlogic\nro.build.display.id=MGCTV152F20210607\n'
 b'ro.build.fingerprint=Amlogic/ampere/ampere:9/PI/20190625:userdebug/release-keys\n'
)
class IdentityTests(unittest.TestCase):
    def test_exact_three_changes(self):
        out=ident.patch(ORIG)
        self.assertIn(b'ro.product.model=m6cw4k\n',out)
        self.assertIn(b'ro.product.brand=LAKI\n',out)
        self.assertIn(b'ro.build.display.id=LAKI Hybrid V6 FULL AUDIO by DarkoBG\n',out)
        self.assertIn(b'ro.product.name=N5MAX\n',out)
        self.assertIn(b'ro.product.device=N5MAX\n',out)
        self.assertIn(b'ro.product.manufacturer=Amlogic\n',out)
        self.assertIn(b'ro.build.fingerprint=Amlogic/ampere/ampere:9/PI/20190625:userdebug/release-keys\n',out)
        self.assertEqual(len(out.splitlines()),len(ORIG.splitlines()))
    def test_reject_wrong_donor(self):
        with self.assertRaises(ValueError):ident.patch(ORIG.replace(b'N5MAX',b'STOCK',1))
    def test_reject_duplicate_model(self):
        with self.assertRaises(ValueError):ident.patch(ORIG+b'ro.product.model=N5MAX\n')
    def test_reject_missing_property(self):
        with self.assertRaises(ValueError):ident.patch(ORIG.replace(b'ro.product.brand=Amlogic\n',b''))
    def test_reject_nul(self):
        with self.assertRaises(ValueError):ident.patch(ORIG+b'\x00')
    def test_keep_crlf(self):
        x=ORIG.replace(b'\n',b'\r\n')
        y=ident.patch(x)
        self.assertNotIn(b'\n',y.replace(b'\r\n',b''))
    def test_v6_uses_separate_system_helper(self):
        code=(ROOT/'scripts/build_laki_v6.py').read_text()
        self.assertIn('patch_v6_system_identity.sh',code)
        self.assertNotIn("scripts / 'patch_system_partition.sh'",code)
    def test_supported_modes_and_selinux_in_bash(self):
        shell=(ROOT/'scripts/patch_v6_system_identity.sh').read_text()
        self.assertIn("'0600'",shell)
        self.assertIn("'0644'",shell)
        self.assertIn('security.selinux',shell)
        self.assertIn('ea_set -f',shell)
        self.assertIn('e2fsck -fy',shell)
        self.assertIn('xml_target=/etc/default-permissions/laki-bluetooth.xml',shell)

if __name__=='__main__':unittest.main()
