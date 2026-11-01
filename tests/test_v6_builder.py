"""V6 safety tests using only synthetic text/dummy files; no vendor blobs."""
from __future__ import annotations
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import build_laki_v6 as v6

MANIFEST = ('''[LIST_NORMAL]
file="DDR.USB" main_type="USB" sub_type="DDR"
file="DDR.USB" main_type="USB" sub_type="UBOOT"
file="aml_sdc_burn.UBOOT" main_type="UBOOT" sub_type="aml_sdc_burn"
file="aml_sdc_burn.ini" main_type="ini" sub_type="aml_sdc_burn"
file="_aml_dtb.PARTITION" main_type="dtb" sub_type="meson1"
file="platform.conf" main_type="conf" sub_type="platform"
[LIST_VERIFY]
'''+''.join(f'file="{n}" main_type="PARTITION" sub_type="{n.split(".")[0]}"\n' for n in sorted(v6.EXPECTED_PARTITIONS))+'''file="DDR.USB" main_type="PARTITION" sub_type="bootloader"
''').encode('ascii')

class SafetyTests(unittest.TestCase):
    def test_valid_full_manifest(self):
        v6.check_full_manifest(MANIFEST)

    def test_missing_bootloader(self):
        text=MANIFEST.replace(b'file="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n',b'')
        with self.assertRaisesRegex(v6.BuildRefused,'bootloader'):
            v6.check_full_manifest(text)

    def test_duplicate_bootloader(self):
        line=b'file="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n'
        with self.assertRaisesRegex(v6.BuildRefused,'bootloader'):
            v6.check_full_manifest(MANIFEST+line)

    def test_duplicate_manifest_entry(self):
        with self.assertRaisesRegex(v6.BuildRefused,'Duplicate'):
            v6.check_full_manifest(MANIFEST+b'file="boot.PARTITION" main_type="PARTITION" sub_type="boot"\n')

    def test_incomplete_stage(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            (d/'image.cfg').write_bytes(MANIFEST)
            with self.assertRaisesRegex(v6.BuildRefused,'Missing required'):
                v6.check_stage_contents(d)

    def test_changed_bytes_refused_by_file_set(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'stage',Path(t)/'verify';a.mkdir();b.mkdir()
            for n in v6.SOURCE_FILES:
                (a/n).write_bytes(MANIFEST if n=='image.cfg' else (n+'123').encode())
                (b/n).write_bytes((a/n).read_bytes())
            verified=v6.file_set_equal(a,b)
            self.assertGreaterEqual(len(verified),14)
            (b/'vendor.PARTITION').write_bytes(b'corrupted')
            with self.assertRaisesRegex(v6.BuildRefused,'SHA-256 mismatch'):
                v6.file_set_equal(a,b)

    def test_wrong_donor_hash_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'DDR.USB';f.write_bytes(b'wrong donor')
            with self.assertRaisesRegex(v6.BuildRefused,'Unexpected source'):
                v6.pin_file(f,'x96_ddr')

    def test_existing_output_dir_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            x=root/'x.img';m=root/'m.img';pack=root/'packer.exe'
            
            with x.open('wb') as f:f.truncate(300*1024**2+1)
            with m.open('wb') as f:f.truncate(300*1024**2+1)
            pack.write_text('fake')
            output=root/'exists';output.mkdir()
            with self.assertRaisesRegex(v6.BuildRefused,'already exists'):
                v6.prerequisites(x,m,pack,output,ROOT/'scripts',require_wsl=False)

    def test_existing_output_never_removed(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'existing';out.mkdir()
            (out/'critical.txt').write_text('keep')
            with self.assertRaisesRegex(v6.BuildRefused,'already exists'):
                v6.prerequisites(Path(t)/'badx',Path(t)/'badm',Path(t)/'badpacker',out,ROOT/'scripts',require_wsl=False)
            self.assertEqual((out/'critical.txt').read_text(),'keep')

    def test_no_vendor_blob_in_script(self):
        for p in (ROOT/'scripts').glob('*.py'):
            self.assertLess(p.stat().st_size, 100000)

if __name__=='__main__':unittest.main()
