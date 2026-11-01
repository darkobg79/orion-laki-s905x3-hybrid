"""Self-contained, offline safety tests (no proprietary firmware blobs)."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_laki_v51_full_audio as audio
import patch_v4_partitions_offline as bootpatch


class AudioBuildSafetyTests(unittest.TestCase):
    def test_expected_build_identity(self):
        self.assertEqual(len(audio.EXPECTED_V5_FULL_SHA256), 64)
        self.assertEqual(audio.AUDIO_PARTS, ("boot.PARTITION", "_aml_dtb.PARTITION"))
        self.assertEqual(len(bootpatch.LIVE_SHA), 64)

    def test_full_manifest_accepts_only_x96_ddr(self):
        normal = '[LIST_NORMAL]\nfile="DDR.USB" main_type="USB" sub_type="DDR"\n'
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'image.cfg'
            config.write_text(normal + '[LIST_VERIFY]\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n')
            audio.check_manifest_full(Path(tmp))
            config.write_text(normal + '[LIST_VERIFY]\nfile="Evil.USB" main_type="PARTITION" sub_type="bootloader"\n')
            with self.assertRaisesRegex(audio.Refusal, 'DDR.USB'):
                audio.check_manifest_full(Path(tmp))
            config.write_text(normal + '[LIST_VERIFY]\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n')
            with self.assertRaisesRegex(audio.Refusal, 'DDR.USB'):
                audio.check_manifest_full(Path(tmp))

    def test_bootloader_in_other_section_is_not_counted(self):
        cfg = b'[LIST_NORMAL]\nfile="other" main_type="PARTITION" sub_type="bootloader"\n[LIST_VERIFY]\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n'
        self.assertEqual(audio.count_bootloader_records(cfg), 1)

    def test_manifest_order_independence(self):
        a = b'[LIST_VERIFY]\nfile="boot.PARTITION" main_type="PARTITION" sub_type="boot"\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n'
        b = b'[LIST_VERIFY]\nsub_type="bootloader" file="DDR.USB" main_type="PARTITION"\nmain_type="PARTITION" sub_type="boot" file="boot.PARTITION"\n'
        self.assertEqual(audio.canonical_manifest(a), audio.canonical_manifest(b))

    @staticmethod
    def populate(root: Path):
        root.mkdir()
        names = (
            "boot.PARTITION", "_aml_dtb.PARTITION", "system.PARTITION", "vendor.PARTITION",
            "product.PARTITION", "odm.PARTITION", "recovery.PARTITION", "dtbo.PARTITION",
            "logo.PARTITION", "vbmeta.PARTITION", "DDR.USB", "aml_sdc_burn.UBOOT",
            "platform.conf", "aml_sdc_burn.ini"
        )
        for name in names:
            (root / name).write_bytes(name.encode('ascii'))
        (root / 'image.cfg').write_text(
            '[LIST_NORMAL]\nfile="DDR.USB" main_type="USB" sub_type="DDR"\n'
            '[LIST_VERIFY]\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n'
            'file="boot.PARTITION" main_type="PARTITION" sub_type="boot"\n',
            encoding='latin1',
        )

    def test_repack_exactly_two_changes_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.populate(base/'source')
            shutil.copytree(base/'source', base/'stage')
            for name in audio.AUDIO_PARTS:
                (base/'stage'/name).write_bytes(b'PATCHED '+name.encode())
            shutil.copytree(base/'stage', base/'verify')
            with patch.object(audio, 'check_ddr_uboot', return_value=None):
                verified = audio.verify_repacked(base/'source', base/'stage', base/'verify')
            self.assertEqual(verified['system.PARTITION'], audio.sha256(base/'source'/'system.PARTITION'))
            self.assertEqual(verified['vendor.PARTITION'], audio.sha256(base/'source'/'vendor.PARTITION'))

    def test_unexpected_vendor_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.populate(base/'source')
            shutil.copytree(base/'source', base/'stage')
            (base/'stage'/'vendor.PARTITION').write_bytes(b'WRONG VENDOR')
            shutil.copytree(base/'stage', base/'verify')
            with patch.object(audio, 'check_ddr_uboot', return_value=None):
                with self.assertRaisesRegex(audio.Refusal, 'vendor.PARTITION'):
                    audio.verify_repacked(base/'source', base/'stage', base/'verify')

    def test_verification_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.populate(base/'source')
            shutil.copytree(base/'source', base/'stage')
            shutil.copytree(base/'stage', base/'verify')
            (base/'verify'/'boot.PARTITION').write_bytes(b'CORRUPTED')
            with patch.object(audio, 'check_ddr_uboot', return_value=None):
                with self.assertRaisesRegex(audio.Refusal, 'boot.PARTITION'):
                    audio.verify_repacked(base/'source', base/'stage', base/'verify')

    def test_local_reference_dtb_is_mandatory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with self.assertRaisesRegex(audio.Refusal, 'referentni DTB'):
                audio.build(base/'v5.img', base/'v41.img', base/'packer.exe', base/'result', base/'missing.dtb', preflight=True)
            reference = base/'reference.dtb'
            reference.write_bytes(b'UNEXPECTED DTB')
            with self.assertRaisesRegex(audio.Refusal, 'SHA256'):
                audio.build(base/'v5.img', base/'v41.img', base/'packer.exe', base/'result', reference, preflight=True)


if __name__ == '__main__':
    unittest.main()
