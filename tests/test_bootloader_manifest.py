"""Offline-only tests: safe manifest identification and FULL entry insertion."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


finalizer = load("laki_finalizer", "scripts/finalize_laki_v5.py")
full = load("laki_full", "scripts/build_laki_v5_full.py")


class BootloaderManifestTests(unittest.TestCase):
    def test_no_bootloader_is_allowed(self):
        cfg = '[LIST_VERIFY]\nfile="boot.PARTITION" main_type="PARTITION" sub_type="boot"\n'
        finalizer.forbid_bootloader_in_listverify(cfg)

    def test_real_bootloader_record_is_rejected(self):
        cfg = ('[LIST_VERIFY]\n'
               'file="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n')
        with self.assertRaisesRegex(RuntimeError, "bootloader"):
            finalizer.forbid_bootloader_in_listverify(cfg)

    def test_attribute_order_and_spacing_are_supported(self):
        cfg = ('[LIST_VERIFY]\n'
               'sub_type = "bootloader" file="DDR.USB" main_type = "PARTITION"\n')
        with self.assertRaisesRegex(RuntimeError, "bootloader"):
            finalizer.forbid_bootloader_in_listverify(cfg)

    def test_entry_in_other_section_does_not_trigger_false_positive(self):
        cfg = ('[OTHER]\nfile="DDR.USB" main_type="PARTITION" sub_type="bootloader"\n'
               '[LIST_VERIFY]\nfile="boot.PARTITION" main_type="PARTITION" sub_type="boot"\n')
        finalizer.forbid_bootloader_in_listverify(cfg)

    def test_full_adds_exactly_one_bootloader_entry(self):
        cfg = ('[LIST_NORMAL]\n'
               'file="DDR.USB" main_type="USB" sub_type="DDR"\n'
               'file="DDR.USB" main_type="USB" sub_type="UBOOT"\n'
               '[LIST_VERIFY]\n'
               'file="boot.PARTITION" main_type="PARTITION" sub_type="boot"\n')
        result = full.add_bootloader_entry(cfg.encode("latin1")).decode("latin1")
        self.assertEqual(full.manifest_bootloader_count(result), 1)
        with self.assertRaisesRegex(RuntimeError, "bootloader"):
            finalizer.forbid_bootloader_in_listverify(result)


if __name__ == "__main__":
    unittest.main()
