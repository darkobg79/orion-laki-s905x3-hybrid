#!/usr/bin/env python3
"""LAKI Hybrid V5 finalizer: never flashes hardware and never modifies V4 source."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ORIG_V4_SHA256 = "D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF"
BASE = Path(r"C:\LakiBox-Backup")
SRC = BASE / "LakiHybrid-V4-NOBOOTLOADER"
ORIG_IMG = BASE / "LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img"
STAGE = BASE / "LakiHybrid-V5-FINAL"
FINAL_IMG = BASE / "LAKI-Hybrid-V5-FINAL-WiFi-BT.img"
CHECK = BASE / "LakiHybrid-V5-FINAL-VERIFY"
WORK = BASE / "LakiHybrid-V5-FINAL-WORK"
SYSTEM_PARTITION_LIMIT = 1_342_177_280  # measured on LAKI hardware: 1280 MiB
KIT = Path(__file__).resolve().parent


def abort(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()


def run(args: list[str], *, label: str, cwd: Path | None = None) -> str:
    print(f"\n== {label} ==", flush=True)
    result = subprocess.run(args, text=True, errors="replace", stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False, cwd=str(cwd) if cwd else None)
    print(result.stdout[-12000:], flush=True)
    if result.returncode:
        abort(f"Failed ({result.returncode}): {label}. Command: {args[0]}")
    return result.stdout


def wslpath(win: Path) -> str:
    text = run(["wsl.exe", "-e", "wslpath", "-a", "-u", str(win)], label="Resolve WSL path")
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines or not lines[-1].startswith("/"):
        abort(f"WSL could not resolve {win}")
    return lines[-1]


def find_packer(explicit: Path | None) -> Path:
    if explicit:
        if not explicit.is_file():
            abort(f"AmlImagePack.exe not found: {explicit}")
        return explicit
    candidates = [
        Path(r"C:\AmlogicKitchen\AmlImagePack.exe"),
        Path(r"C:\AmlogicKitchen\bin\AmlImagePack.exe"),
        Path(r"C:\AmlogicKitchen\tools\AmlImagePack.exe"),
        BASE / "AmlImagePack.exe",
    ]
    found = shutil.which("AmlImagePack.exe")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    basekitchen = Path(r"C:\AmlogicKitchen")
    if basekitchen.is_dir():
        for item in basekitchen.rglob("AmlImagePack.exe"):
            if item.is_file():
                return item
    abort("AmlImagePack.exe not found. Re-run with --packer C:\\path\\AmlImagePack.exe")


def forbid_bootloader_in_listverify(cfg: str) -> None:
    # Reject inadvertent restoration of the known bootloader verification/flash entry.
    if re.search(r'(?im)^\s*\[LIST_VERIFY\]\s+[^\r\n]*sub_type\s*=\s*["\']?bootloader', cfg):
        abort("Found bootloader [LIST_VERIFY] entry! Refusing to create purported NOBOOTLOADER final ROM.")


def verify_images(src: Path, dst: Path, *, omit_system: bool, verify_cfg: bool = True) -> dict[str, str]:
    verified = {}
    for item in sorted(src.iterdir()):
        if not item.is_file():
            continue
        if item.name == "system.PARTITION" and omit_system:
            continue
        if item.name in ("image.cfg", "platform.conf") and not verify_cfg:
            continue
        if item.suffix not in (".PARTITION", ".UBOOT", ".USB") and item.name not in ("image.cfg", "platform.conf"):
            continue
        other = dst / item.name
        if not other.is_file():
            abort(f"Missing verification file: {other}")
        s1, s2 = sha256(item), sha256(other)
        if s1 != s2:
            abort(f"SHA mismatch {item.name}: expected {s1}, found {s2}")
        verified[item.name] = s1
    if not verified:
        abort("No partition images verified")
    return verified


def main() -> None:
    global BASE, SRC, ORIG_IMG, STAGE, FINAL_IMG, CHECK, WORK
    p = argparse.ArgumentParser(description="Patch the proven V4 firmware's Android default permission and repack safely. No flash action.")
    p.add_argument("--base", type=Path, default=BASE, help="Directory containing V4 folder and V4 .img (default C:\\LakiBox-Backup)")
    p.add_argument("--packer", type=Path, help="Exact path of previously working AmlImagePack.exe")
    p.add_argument("--skip-v4-image-hash", action="store_true", help="Only if the already-known V4 file was renamed/rebuilt; not recommended")
    args = p.parse_args()
    BASE = args.base.resolve()
    SRC = BASE / "LakiHybrid-V4-NOBOOTLOADER"
    ORIG_IMG = BASE / "LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img"
    STAGE = BASE / "LakiHybrid-V5-FINAL"
    FINAL_IMG = BASE / "LAKI-Hybrid-V5-FINAL-WiFi-BT.img"
    CHECK = BASE / "LakiHybrid-V5-FINAL-VERIFY"
    WORK = BASE / "LakiHybrid-V5-FINAL-WORK"
    if os.name != "nt":
        abort("This entrypoint is for Windows; use WSL only for the included patch_system_partition.sh.")
    report_file = BASE / "LAKI-Hybrid-V5-FINAL-BUILD-REPORT.json"
    for item in (STAGE, WORK, CHECK, FINAL_IMG, report_file):
        if item.exists():
            abort(f"Refusing to overwrite existing output: {item}. Review or rename it first.")
    required = ["image.cfg", "system.PARTITION", "vendor.PARTITION", "boot.PARTITION", "_aml_dtb.PARTITION", "DDR.USB", "aml_sdc_burn.UBOOT"]
    for name in required:
        if not (SRC / name).is_file():
            abort(f"Required V4 stage file missing: {SRC / name}")
    if not ORIG_IMG.is_file():
        abort(f"Original working V4 .img not found: {ORIG_IMG}")
    xml = KIT / "laki-bluetooth-default-permissions.xml"
    sh = KIT / "patch_system_partition.sh"
    if not xml.is_file() or not sh.is_file():
        abort("Kit missing XML or shell script")
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml)
    if tree.getroot().tag != "exceptions":
        abort("Invalid permission file")
    packer = find_packer(args.packer)
    v4img_sha = sha256(ORIG_IMG)
    print("Known V4 image SHA256:", v4img_sha)
    if v4img_sha != ORIG_V4_SHA256 and not args.skip_v4_image_hash:
        abort("V4 image hash is NOT the known successfully flashed firmware; refusing. Check source.")
    cfg = (SRC / "image.cfg").read_text(encoding="latin1")
    forbid_bootloader_in_listverify(cfg)
    free = shutil.disk_usage(BASE).free
    # Ext4 conversion 1.28GiB + output .img ~1.35GB + 1.28GB sparse roundtrip + copy stage.
    # 7 GiB is a conservative estimate given previously measured image size.
    if free < 7 * 1024**3:
        abort(f"Not enough free space for safe staging+roundtrip: {free / (1024**3):.2f} GiB (need 7 GiB)")
    run(["wsl.exe", "-e", "bash", "-lc", "command -v simg2img && command -v img2simg && command -v debugfs && command -v e2fsck"], label="Check WSL tools")
    print("\n[1/4] Copying V4 to a new staging folder (original remains unchanged)...")
    shutil.copytree(SRC, STAGE)
    stage_file = STAGE / "system.PARTITION"
    before_system = sha256(stage_file)
    verified_unchanged = verify_images(SRC, STAGE, omit_system=False)
    print(f"[2/4] Patching system.PARTITION in {STAGE}")
    run(["wsl.exe", "-e", "bash", wslpath(sh), wslpath(stage_file),
         wslpath(xml), wslpath(WORK), str(SYSTEM_PARTITION_LIMIT)], label="Offline ext4 patch and sparse roundtrip")
    if sha256(stage_file) == before_system:
        abort("System partition was NOT modified. Aborting.")
    verify_images(SRC, STAGE, omit_system=True)
    if (SRC / "image.cfg").read_bytes() != (STAGE / "image.cfg").read_bytes():
        abort("image.cfg changed unexpectedly")
    print("[3/4] Repacking FINAL Amlogic USB Burning Tool image...")
    run([str(packer), "-r", str(STAGE / "image.cfg"), str(STAGE), str(FINAL_IMG)], label="AmlImagePack -r", cwd=packer.parent)
    if not FINAL_IMG.is_file() or FINAL_IMG.stat().st_size < 300 * 1024**2:
        abort("Packed output missing or suspiciously small. Do not flash.")
    final_sha = sha256(FINAL_IMG)
    print("[4/4] Unpacking FINAL image again, then verifying partition SHA256...")
    CHECK.mkdir(parents=True, exist_ok=False)
    run([str(packer), "-d", str(FINAL_IMG), str(CHECK)], label="AmlImagePack -d offline validation", cwd=packer.parent)
    verified_inside = verify_images(STAGE, CHECK, omit_system=False, verify_cfg=False)
    report = {
        "status": "PACKED AND OFFLINE-VERIFIED; NOT HARDWARE-TESTED OR FACTORY-RESET-TESTED",
        "model": "LAKI AC213 2GB / Magicsee Unisoc kernel/vendor + X96 bootloader",
        "change": "Only system.PARTITION: /etc/default-permissions/laki-bluetooth.xml adds READ_CONTACTS grant to com.android.bluetooth (fixed=false)",
        "known_v4_sha256": v4img_sha,
        "final_image": str(FINAL_IMG),
        "final_sha256": final_sha,
        "final_bytes": FINAL_IMG.stat().st_size,
        "verified_partition_files": verified_inside,
        "notes": ["Do NOT erase flash/bootloader", "Test on device without deleting working firmware", "Factory reset behavior untested", "Do NOT claim Bluetooth audio until on-device pairing test"],
    }
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nSUCCESS: Final packed image ready for controlled testing (not yet tested on hardware):")
    print(FINAL_IMG)
    print("SHA256:", final_sha)
    print("Report:", report_file)
    print("Original V4 firmware and original staged folder remain untouched.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nSTOP - build incomplete / NOT a validated final firmware:", exc, file=sys.stderr)
        sys.exit(1)
