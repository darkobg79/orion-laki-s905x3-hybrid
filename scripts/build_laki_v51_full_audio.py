#!/usr/bin/env python3
"""Compose a new LAKI V5.1 FULL AUDIO image from TWO previously packed images.

Source A: exactly the offline-verified V5 FULL X96 BOOTLOADER image.
Source B: user-proven V4.1 audio eARC-off test image.

The ONLY payload changes relative to Source A may be boot.PARTITION and
_aml_dtb.PARTITION, and BOTH must match an independently re-computed, narrowly
scoped eARC patch of Source A. Repack + unpack + SHA256-verify all payloads.

Runs on Windows. NEVER flashes a device. Never modifies inputs.
The proprietary source DTB must be provided locally with --reference-dtb;
it is deliberately NOT published in the source repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from patch_laki_earc import parse
from patch_v4_partitions_offline import (
    LIVE_SHA, aml_entries, change_boot, get_prop, patch_multi, read_boot_second,
)

# This SHA is from the earlier V5 FULL pack+unpack report, NOT the V4.1 image.
EXPECTED_V5_FULL_SHA256 = "AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9"
EXPECTED_DDR_SHA256 = "77CB764B897F59D146178513CC3563EB1499A06F3DCCCB93A3F405C16F999D33"
EXPECTED_UBOOT_SHA256 = "8BE0C10AF6D8FA087ABCEACD7F09D0AA16356B508EDE647E08CDE1E5A4ED0E45"
OUTPUT_IMG = "LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img"
DEFAULT_BASE = Path(r"C:\LakiBox-Backup")
REQUIRED_FILES = (
    "image.cfg", "DDR.USB", "aml_sdc_burn.UBOOT", "boot.PARTITION",
    "_aml_dtb.PARTITION", "system.PARTITION", "vendor.PARTITION",
)
AUDIO_PARTS = ("boot.PARTITION", "_aml_dtb.PARTITION")
SKIP_COMPARE_V41 = set(AUDIO_PARTS) | {"system.PARTITION", "image.cfg"}
PAYLOAD_SUFFIXES = (".PARTITION", ".USB", ".UBOOT")
OTHER_PACKED_FILES = {"platform.conf", "aml_sdc_burn.ini"}


class Refusal(RuntimeError):
    pass


def fail(reason: str) -> None:
    raise Refusal(reason)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def content_hashes(directory: Path) -> dict[str, str]:
    ret = {}
    for p in sorted(directory.iterdir()):
        if p.is_file() and (p.name.endswith(PAYLOAD_SUFFIXES) or p.name in OTHER_PACKED_FILES):
            ret[p.name] = sha256(p)
    return ret


def check_required(folder: Path, required=REQUIRED_FILES) -> None:
    for name in required:
        if not (folder / name).is_file():
            fail(f"Nedostaje obavezan fajl: {folder / name}")


def canonical_manifest(image_cfg: bytes) -> list[tuple[str, str, str, str]]:
    """Canonicalize LIST_NORMAL and LIST_VERIFY records for pack/unpack auditing."""
    section = ""
    entries = []
    for line in image_cfg.decode("latin1").splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith(("#", ";")):
            continue
        if trimmed.startswith("[") and trimmed.endswith("]"):
            section = trimmed.upper()
            continue
        if section in ("[LIST_NORMAL]", "[LIST_VERIFY]"):
            attrs = dict(re.findall(r'([a-zA-Z_]+)\s*=\s*"([^"]+)"', line))
            if not all(key in attrs for key in ("file", "main_type", "sub_type")):
                fail("Neispravan zapis u image.cfg manifestu: " + trimmed)
            entries.append((section, attrs["file"], attrs["main_type"], attrs["sub_type"]))
    if not entries:
        fail("Nema prepoznatih manifest zapisa")
    return sorted(entries)


def bootloader_records(image_cfg: bytes) -> list[str]:
    """Return PARTITION/bootloader filenames from [LIST_VERIFY] only."""
    section = ""
    records: list[str] = []
    for line in image_cfg.decode("latin1").splitlines():
        trimmed = line.strip()
        if trimmed.startswith("[") and trimmed.endswith("]"):
            section = trimmed.upper()
            continue
        if section != "[LIST_VERIFY]" or not trimmed or trimmed.startswith(("#", ";")):
            continue
        attrs = dict(re.findall(r'([a-zA-Z_]+)\s*=\s*"([^"]+)"', trimmed))
        if attrs.get("main_type", "").upper() == "PARTITION" and attrs.get("sub_type", "").lower() == "bootloader":
            records.append(attrs.get("file", ""))
    return records


def count_bootloader_records(image_cfg: bytes) -> int:
    return len(bootloader_records(image_cfg))


def check_manifest_full(folder: Path) -> None:
    records = bootloader_records((folder / "image.cfg").read_bytes())
    if records != ["DDR.USB"]:
        fail(f"FULL image.cfg mora imati tacno jedan PARTITION/bootloader=DDR.USB, nadjeno: {records}")


def check_ddr_uboot(folder: Path) -> None:
    for name, expected in (("DDR.USB", EXPECTED_DDR_SHA256),
                           ("aml_sdc_burn.UBOOT", EXPECTED_UBOOT_SHA256)):
        found = sha256(folder / name)
        if found != expected:
            fail(f"NEPOZNAT DDR/UBOOT: {name}, SHA256={found}; ocekivano {expected}")


def verify_v41_provenance(v5_stage: Path, v41_stage: Path, reference_dtb: Path) -> dict:
    """Validate that V4.1 parts are EXACTLY the minimal patch of the known V5 tree.

    A partially compatible DTB is insufficient. The original V5 parts are patched
    independently, and BOTH outputs must equal the exact payloads inside the V4.1 IMG.
    """
    check_required(v5_stage)
    check_required(v41_stage)
    check_manifest_full(v5_stage)
    check_ddr_uboot(v5_stage)
    check_ddr_uboot(v41_stage)

    # Both images have compatible unchanged hardware/userspace payloads; V5's
    # system.PARTITION legitimately differs because it includes BT permissions.
    old_hashes = content_hashes(v5_stage)
    v41_hashes = content_hashes(v41_stage)
    if len(old_hashes) < 10:
        fail(f"Nedovoljno particija u V5 FULL ({len(old_hashes)})")
    for name, expected in old_hashes.items():
        if name in SKIP_COMPARE_V41:
            continue
        if v41_hashes.get(name) != expected:
            fail(f"V4.1 i V5 FULL se razlikuju u {name}; NIJE samo audio razlika")

    if sha256(reference_dtb).lower() != LIVE_SHA:
        fail("Referentni DTB nije originalni provereni LAKI V4 DTB")
    source_tree = parse(reference_dtb.read_bytes())
    original_dtb = (v5_stage / "_aml_dtb.PARTITION").read_bytes()
    original_boot = (v5_stage / "boot.PARTITION").read_bytes()
    v41_dtb = (v41_stage / "_aml_dtb.PARTITION").read_bytes()
    v41_boot = (v41_stage / "boot.PARTITION").read_bytes()

    # This is the previously verified eARC-off patch function used for V4.1.
    patched_dtb, selected_slot = patch_multi(original_dtb, source_tree)
    patched_boot = change_boot(original_boot, original_dtb, patched_dtb)

    if patched_dtb != v41_dtb:
        fail("V4.1 _aml_dtb.PARTITION nije IDENTICAN ocekivanom eARC-off patchu V5 FULL. STOP.")
    if patched_boot != v41_boot:
        fail("V4.1 boot.PARTITION nije IDENTICAN ocekivanom eARC-off patchu V5 FULL. STOP.")

    # Extra independent check: boot embedded multi-DTB equals standalone DTB.
    import gzip
    second = read_boot_second(v41_boot)[5]
    if gzip.decompress(second) != gzip.decompress(v41_dtb):
        fail("V4.1 boot embedded DTB ne odgovara _aml_dtb.PARTITION")
    raw_multi = gzip.decompress(v41_dtb)
    entries = aml_entries(raw_multi)
    slot_id, offset, slot_len = [x for x in entries if x[0] == selected_slot][0]
    dtb_slot = raw_multi[offset:offset + slot_len]
    dtb_size = int.from_bytes(dtb_slot[4:8], "big")
    selected_tree = parse(dtb_slot[:dtb_size])
    if get_prop(selected_tree, "/soc/bus@ff663000/earc@0", "status") != b"disabled\0":
        fail("Izabrani AC213 DTB nema disabled eARC")
    if "/auge_sound/aml-audio-card,dai-link@6" in selected_tree["nodes"]:
        fail("Izabrani AC213 DTB i dalje ima neispravni eARC DAI link@6")
    if get_prop(selected_tree, "/", "amlogic-dt-id") != b"sm1_ac213_2g\0":
        fail("Izabrani DTB nije sm1_ac213_2g")

    return {
        "checked_board": "sm1_ac213_2g",
        "patched_slot": slot_id,
        "earc_disabled": True,
        "earc_link6_removed": True,
        "other_board_variants_untouched_by_patch": True,
        "v41_boot_matches_recomputed_minimal_patch": True,
        "v41_aml_dtb_matches_recomputed_minimal_patch": True,
        "source_v5_boot_sha256": old_hashes["boot.PARTITION"],
        "source_v5_dtb_sha256": old_hashes["_aml_dtb.PARTITION"],
        "v41_boot_sha256": sha256(v41_stage / "boot.PARTITION"),
        "v41_dtb_sha256": sha256(v41_stage / "_aml_dtb.PARTITION"),
    }


def run_packer(packer: Path, flags: list[str], label: str) -> None:
    print("\n>> " + label, flush=True)
    cmd = [str(packer)] + flags
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, errors="replace", cwd=str(packer.parent), check=False)
    print(process.stdout[-14000:])
    if process.returncode:
        fail(f"{label} je neuspesan, exit code {process.returncode}")


def verify_repacked(v5_unpacked: Path, stage: Path, verify: Path) -> dict[str, str]:
    source = content_hashes(v5_unpacked)
    staged = content_hashes(stage)
    checked = content_hashes(verify)
    if set(source) != set(staged) or set(staged) != set(checked):
        fail(f"Nejednak spisak particija: source={sorted(source)}, stage={sorted(staged)}, verify={sorted(checked)}")
    if len(staged) < 10:
        fail("Previse malo particija za FULL image")
    for name in sorted(staged):
        if checked[name] != staged[name]:
            fail(f"PACK/UNPACK ne odgovara SHA256 za {name}")
        if name not in AUDIO_PARTS and staged[name] != source[name]:
            fail(f"Neplanirana izmena u {name}")
    if (stage / "image.cfg").read_bytes() != (v5_unpacked / "image.cfg").read_bytes():
        fail("image.cfg mora biti neizmenjen u odnosu na V5 FULL")
    check_manifest_full(verify)
    if canonical_manifest((stage / "image.cfg").read_bytes()) != canonical_manifest((verify / "image.cfg").read_bytes()):
        fail("AmlImagePack pack/unpack izmenio manifest zapise u FULL image.cfg")
    check_ddr_uboot(verify)
    return staged


def check_initial_paths(v5_img: Path, v41_img: Path, packer: Path, out_root: Path,
                        minimum_free_bytes: int = 9 * 1024**3) -> dict:
    for p in (v5_img, v41_img, packer):
        if not p.is_file():
            fail(f"Fajl ne postoji: {p}")
    if v5_img.resolve() == v41_img.resolve():
        fail("V5 FULL i V4.1 moraju biti dva razlicita IMG fajla")
    if out_root.exists():
        fail(f"Izlazni direktorijum vec postoji: {out_root}; izaberi novi --output-root")
    if v5_img.stat().st_size < 300 * 1024**2 or v41_img.stat().st_size < 300 * 1024**2:
        fail("IMG je sumnjivo mali (<300 MiB); proveri ulaze")
    have = sha256(v5_img)
    if have != EXPECTED_V5_FULL_SHA256:
        fail(f"V5 FULL nije iz ranije offline proverene slike. SHA256={have}, ocekivano={EXPECTED_V5_FULL_SHA256}")
    free = shutil.disk_usage(out_root.parent).free
    if free < minimum_free_bytes:
        fail(f"Nema dovoljno slobodnog prostora: {free/(1024**3):.2f} GiB, preporuceno bar 9 GiB")
    return {"v5_full_sha256": have, "v41_sha256": sha256(v41_img), "available_free_gib": round(free / (1024**3), 2)}


def build(v5_img: Path, v41_img: Path, packer: Path, out_root: Path, reference_dtb: Path, *, preflight=False) -> dict:
    if not reference_dtb.is_file():
        fail(f"Nedostaje lokalni referentni DTB: {reference_dtb}")
    if sha256(reference_dtb).lower() != LIVE_SHA:
        fail("Lokalni referentni DTB nema ocekivani SHA256; STOP")
    pre = check_initial_paths(v5_img, v41_img, packer, out_root)
    print("\n== Preflight OK ==")
    print(json.dumps(pre, indent=2))
    if preflight:
        return pre

    # By design, this is a new output directory and never touches source images.
    out_root.mkdir(parents=True, exist_ok=False)
    unpack_v5 = out_root / "INPUT-V5-FULL-UNPACKED"
    unpack_v41 = out_root / "INPUT-V4.1-UNPACKED"
    stage = out_root / "V5.1-FULL-AUDIO-STAGE"
    unpack_result = out_root / "V5.1-FULL-AUDIO-VERIFY"
    for folder in (unpack_v5, unpack_v41, unpack_result):
        folder.mkdir(parents=True, exist_ok=False)
    output_img = out_root / OUTPUT_IMG
    report_file = out_root / "LAKI-V5.1-FULL-AUDIO-BUILD-REPORT.json"

    run_packer(packer, ["-d", str(v5_img), str(unpack_v5)], "Unpack pinned V5 FULL source")
    run_packer(packer, ["-d", str(v41_img), str(unpack_v41)], "Unpack tested V4.1 AUDIO source")
    provenance = verify_v41_provenance(unpack_v5, unpack_v41, reference_dtb)
    print("\n== V4.1 audio patch provenance VERIFIED ==")
    print(json.dumps(provenance, indent=2))

    # Stage a full copy, preserving ALL V5 system/vendor and the X96 FULL bootloader.
    shutil.copytree(unpack_v5, stage)
    for name in AUDIO_PARTS:
        shutil.copyfile(unpack_v41 / name, stage / name)
    if (stage / "image.cfg").read_bytes() != (unpack_v5 / "image.cfg").read_bytes():
        fail("image.cfg changed unexpectedly")
    check_manifest_full(stage)
    check_ddr_uboot(stage)

    baseline_hashes = content_hashes(unpack_v5)
    stage_hashes = content_hashes(stage)
    for name, before in baseline_hashes.items():
        if name not in AUDIO_PARTS and stage_hashes.get(name) != before:
            fail(f"Stage altered unexpected V5 component: {name}")
    for name in AUDIO_PARTS:
        if stage_hashes[name] != sha256(unpack_v41 / name):
            fail(f"Stage did not receive V4.1 {name}")

    run_packer(packer, ["-r", str(stage / "image.cfg"), str(stage), str(output_img)], "Pack V5.1 FULL AUDIO")
    if not output_img.is_file() or output_img.stat().st_size < 300 * 1024**2:
        fail("Nema validne .img datoteke ili je neocekivano mala")
    run_packer(packer, ["-d", str(output_img), str(unpack_result)], "Unpack result to reverify every partition")
    checked = verify_repacked(unpack_v5, stage, unpack_result)

    # Source IMG files must remain byte-for-byte identical after the procedure.
    if sha256(v5_img) != pre["v5_full_sha256"] or sha256(v41_img) != pre["v41_sha256"]:
        fail("Jedan od ulaznih IMG fajlova promenjen tokom rada!")

    report = {
        "status": "PACKED AND OFFLINE VERIFIED ONLY; NOT FLASH-TESTED, NOT STOCK-BOOTLOADER-TESTED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "result_image": str(output_img),
        "result_image_sha256": sha256(output_img),
        "result_image_bytes": output_img.stat().st_size,
        "source_v5_full": str(v5_img),
        "source_v5_full_sha256": pre["v5_full_sha256"],
        "source_v41": str(v41_img),
        "source_v41_sha256": pre["v41_sha256"],
        "provenance": provenance,
        "source_payload_sha256": baseline_hashes,
        "final_payload_sha256": checked,
        "changed_payloads": list(AUDIO_PARTS),
        "system_is_unchanged_from_v5": baseline_hashes["system.PARTITION"] == checked["system.PARTITION"],
        "vendor_is_unchanged_from_v5": baseline_hashes["vendor.PARTITION"] == checked["vendor.PARTITION"],
        "full_manifest_has_one_bootloader_partition": True,
        "x96_ddr_and_uboot_sha256_verified": True,
        "notes": [
            "USB Burning Tool FULL risk: X96 PARTITION/bootloader is explicitly present.",
            "The first LAKI unit had already been flashed with the X96 bootloader before V4.1 testing.",
            "Full image MUST NOT be assumed safe on an untouched Orion bootloader or other PCB revisions.",
            "Do not enable Erase bootloader, Erase flash or Overwrite key without independent recovery validation.",
            "V5 Bluetooth default READ_CONTACTS permission remains untested on a clean device.",
            "MEDIA audio may be inaudible at low index. On tested V4.1, Android stream 3 volume 50/65 worked.",
            "No IMG was uploaded or distributed by this toolkit; all firmware inputs are local."
        ],
    }
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n" + "=" * 72)
    print("SUCCESS: PACKED AND OFFLINE VERIFIED (NOT TESTED ON HARDWARE)")
    print("Image: ", output_img)
    print("SHA256:", report["result_image_sha256"])
    print("Report:", report_file)
    print("Only boot.PARTITION and _aml_dtb.PARTITION differ from the original V5 FULL.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Windows source image directory")
    parser.add_argument("--v5-full-img", type=Path, help="V5 FULL image from original offline build")
    parser.add_argument("--v41-img", type=Path, help="Tested V4.1 AUDIO eARC OFF IMG")
    parser.add_argument("--packer", type=Path, default=Path(r"C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"))
    parser.add_argument("--output-root", type=Path, help="Brand-new directory; originals are never overwritten")
    parser.add_argument("--reference-dtb", type=Path, required=True, help="Local laki-v4-running.dtb (SHA256 pinned); binary not distributed")
    parser.add_argument("--check-only", action="store_true", help="Preflight no-write: SHA256, files, disk space")
    args = parser.parse_args()
    if os.name != "nt":
        fail("Pokreni na Windows 10/11 (CMD ili PowerShell), ne u WSL/Linux")
    base = args.base.resolve()
    v5 = (args.v5_full_img or (base / "LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img")).resolve()
    v41 = (args.v41_img or (base / "LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img")).resolve()
    packer = args.packer.resolve()
    out = (args.output_root or (base / "LAKI-V5.1-FULL-AUDIO-BUILD")).resolve()
    return build(v5, v41, packer, out, args.reference_dtb.resolve(), preflight=args.check_only)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nSTOP: NIJE DOBIJEN VERIFIKOVAN FULL AUDIO IMG: " + str(exc), file=sys.stderr)
        sys.exit(1)
