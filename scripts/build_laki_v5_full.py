#!/usr/bin/env python3
"""Build a separate Amlogic V5 FULL image from already verified V5 NOBOOTLOADER stage.

Offline only. Never flashes a device or modifies the source staging image/folder.
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
from pathlib import Path

BASE_DEFAULT = Path(r"C:\LakiBox-Backup")
DDR_SHA = "77CB764B897F59D146178513CC3563EB1499A06F3DCCCB93A3F405C16F999D33"
UBOOT_SHA = "8BE0C10AF6D8FA087ABCEACD7F09D0AA16356B508EDE647E08CDE1E5A4ED0E45"
BOOTLOADER_LINE = 'file="DDR.USB"\t\tmain_type="PARTITION"\t\tsub_type="bootloader"'


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as fd:
        for chunk in iter(lambda: fd.read(8*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()


def fail(reason: str):
    raise RuntimeError(reason)


def run(argv: list[str], label: str, cwd: Path | None = None):
    print(f"\n== {label} ==", flush=True)
    r = subprocess.run(argv, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, errors='replace')
    print(r.stdout[-16000:], flush=True)
    if r.returncode:
        fail(f"{label} failed with code {r.returncode}")


def find_packer(given: Path | None, base: Path) -> Path:
    if given:
        if not given.is_file():
            fail(f"Missing packer: {given}")
        return given
    candidates = [
        Path(r"C:\AmlogicKitchen\AmlImagePack.exe"),
        Path(r"C:\AmlogicKitchen\bin\AmlImagePack.exe"),
        Path(r"C:\AmlogicKitchen\tools\AmlImagePack.exe"),
        base / "AmlImagePack.exe",
    ]
    located = shutil.which("AmlImagePack.exe")
    if located:
        candidates.append(Path(located))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    kitchen = Path(r"C:\AmlogicKitchen")
    if kitchen.is_dir():
        for candidate in kitchen.rglob('AmlImagePack.exe'):
            if candidate.is_file():
                return candidate
    fail('Cannot locate AmlImagePack.exe; use --packer "C:\\full\\path\\AmlImagePack.exe"')


def manifest_bootloader_count(text: str) -> int:
    """Count PARTITION/bootloader entries inside [LIST_VERIFY] only."""
    section = ''
    n = 0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            section = s.upper()
            continue
        if section == '[LIST_VERIFY]' and 'main_type="PARTITION"' in s and 'sub_type="bootloader"' in s:
            n += 1
    return n


def add_bootloader_entry(raw: bytes) -> bytes:
    """Restores exactly the X96 DDR.USB verification/partition flash declaration."""
    text = raw.decode('latin1')
    if manifest_bootloader_count(text):
        fail('Input already has a bootloader verify entry; refusing duplicate')
    if '[LIST_VERIFY]' not in text:
        fail('Missing [LIST_VERIFY] section in image.cfg')
    if not re.search(r'(?m)^file="DDR\.USB"\s+main_type="USB"\s+sub_type="DDR"\s*$', text):
        fail('image.cfg does not declare expected DDR.USB USB DDR record')
    if not re.search(r'(?m)^file="DDR\.USB"\s+main_type="USB"\s+sub_type="UBOOT"\s*$', text):
        fail('image.cfg does not declare expected DDR.USB USB UBOOT record')
    boot = re.search(r'(?m)^(file="boot\.PARTITION"\s+main_type="PARTITION"\s+sub_type="boot")[ \t]*(\r?\n)', text)
    if not boot or text.find('[LIST_VERIFY]') > boot.start():
        fail('Cannot find expected boot.PARTITION declaration in image.cfg')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    position = boot.end()
    patched = text[:position] + BOOTLOADER_LINE + newline + text[position:]
    if manifest_bootloader_count(patched) != 1 or patched.replace(BOOTLOADER_LINE + newline, '', 1) != text:
        fail('Manifest patch verification failed')
    return patched.encode('latin1')


def verified_artifacts(stage: Path, unpacked: Path, *, compare_cfg: bool = False) -> dict[str, str]:
    result = {}
    for original in sorted(stage.iterdir()):
        if not original.is_file():
            continue
        if original.suffix not in ('.USB', '.UBOOT', '.PARTITION') and original.name not in ('platform.conf', 'aml_sdc_burn.ini'):
            continue
        match = unpacked / original.name
        if not match.is_file():
            fail(f'Missing file in unpacked image: {match}')
        h1, h2 = sha256(original), sha256(match)
        if h1 != h2:
            fail(f'Packed/unpacked SHA256 mismatch: {original.name} (source {h1}; unpacked {h2})')
        result[original.name] = h1
    if len(result) < 8:
        fail(f'Too few files verified ({len(result)}). Refuse incomplete firmware.')
    if compare_cfg:
        if (stage / 'image.cfg').read_bytes() != (unpacked / 'image.cfg').read_bytes():
            fail('Manifest differs after unpack')
    return result


def main():
    if os.name != 'nt':
        fail('Run this builder in Windows CMD, not Linux/WSL')
    p = argparse.ArgumentParser(description='Make V5 FULL from V5 NOBOOTLOADER with SHA256-verified X96 bootloader. Offline only.')
    p.add_argument('--base', type=Path, default=BASE_DEFAULT)
    p.add_argument('--packer', type=Path)
    args = p.parse_args()
    base = args.base.resolve()
    src = base / 'LakiHybrid-V5-FINAL'
    src_img = base / 'LAKI-Hybrid-V5-FINAL-WiFi-BT.img'
    src_report = base / 'LAKI-Hybrid-V5-FINAL-BUILD-REPORT.json'
    stage = base / 'LakiHybrid-V5-FULL-X96-BOOTLOADER'
    dest = base / 'LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img'
    verify = base / 'LakiHybrid-V5-FULL-VERIFY'
    dest_report = base / 'LAKI-Hybrid-V5-FULL-BUILD-REPORT.json'
    for path in [stage, dest, verify, dest_report]:
        if path.exists():
            fail(f'Output already exists, refusing to overwrite: {path}')
    for path in [src/'image.cfg', src/'DDR.USB', src/'aml_sdc_burn.UBOOT', src/'system.PARTITION',
                 src/'boot.PARTITION', src/'vendor.PARTITION', src_img, src_report]:
        if not path.is_file():
            fail(f'Required verified V5 input missing: {path}')
    report = json.loads(src_report.read_text(encoding='utf-8-sig'))
    if not str(report.get('status', '')).startswith('PACKED AND OFFLINE-VERIFIED'):
        fail('V5 report does not indicate successful offline verification')
    if sha256(src_img) != report.get('final_sha256'):
        fail('V5 image sha256 does not match V5 build report')
    listed = report.get('verified_partition_files', {})
    if not isinstance(listed, dict) or len(listed) < 8:
        fail('V5 build report has no complete SHA256 partition list')
    for name, expected in listed.items():
        check_path = src/name
        if not check_path.is_file() or sha256(check_path) != expected:
            fail(f'V5 staging file missing/modified since build: {name}')
    if sha256(src/'DDR.USB') != DDR_SHA or sha256(src/'aml_sdc_burn.UBOOT') != UBOOT_SHA:
        fail('Bootloader DDR/UBOOT SHA256 is not the VERIFIED X96 working pair; refusing FULL build')
    orig_cfg = (src/'image.cfg').read_bytes()
    full_cfg = add_bootloader_entry(orig_cfg)
    if shutil.disk_usage(base).free < 5*1024**3:
        fail('Need at least 5 GiB free on destination volume for full staging, packing and verification')
    packer = find_packer(args.packer, base)
    print('Source V5 verified:', src_img)
    print('Source V5 SHA256:', sha256(src_img))
    print('X96 DDR.USB SHA256:', DDR_SHA)
    print('X96 UBOOT SHA256:', UBOOT_SHA)
    print('Creating FULL staging copy...')
    shutil.copytree(src, stage)
    (stage/'image.cfg').write_bytes(full_cfg)
    if (stage/'image.cfg').read_bytes() != full_cfg:
        fail('Cannot verify patched stage manifest')
    # Immutable: all original V5 content is byte-for-byte equal except image.cfg
    for name, expected in listed.items():
        if sha256(stage/name) != expected:
            fail(f'Stage modified unexpected file {name}')
    print('Packing FULL image with X96 PARTITION/bootloader record...')
    run([str(packer), '-r', str(stage/'image.cfg'), str(stage), str(dest)], 'AmlImagePack -r FULL', cwd=packer.parent)
    if not dest.is_file() or dest.stat().st_size < 300*1024**2:
        fail('Result .img absent or suspiciously small; do not flash')
    print('Unpacking FULL image for independent SHA256 validation...')
    verify.mkdir(parents=True, exist_ok=False)
    run([str(packer), '-d', str(dest), str(verify)], 'AmlImagePack -d FULL check', cwd=packer.parent)
    files = verified_artifacts(stage, verify)
    unpacked_manifest = verify/'image.cfg'
    if not unpacked_manifest.exists() or manifest_bootloader_count(unpacked_manifest.read_text(encoding='latin1')) != 1:
        fail('Unpacked FULL image does NOT declare single PARTITION/bootloader; refuse image')
    result = {
        'status': 'OFFLINE VERIFIED ONLY — FULL BOOTLOADER FLASH NOT TESTED ON A SECOND BOX',
        'source_v5_img': str(src_img),
        'source_v5_sha256': sha256(src_img),
        'full_img': str(dest),
        'full_sha256': sha256(dest),
        'full_size': dest.stat().st_size,
        'bootloader_source': 'Known-working X96 Max Plus 5 DDR.USB and aml_sdc_burn.UBOOT',
        'bootloader_partition_entry': BOOTLOADER_LINE,
        'bootloader_verified_ddr_sha256': DDR_SHA,
        'bootloader_verified_uboot_sha256': UBOOT_SHA,
        'verified_files': files,
        'warnings': [
            'INCLUSION does not guarantee programming; USB Burning Tool options govern actual flash behavior.',
            'Before FULL flash check same SoC, RAM, eMMC, board revision, and recoverability.',
            'Erase flash / Erase bootloader are destructive; do not enable until hardware compatibility and recovery are confirmed.',
            'Never use the previously failing Magicsee bootloader; this image uses only the successful X96 pair.',
            'Bluetooth V5 fresh-install permission grant remains untested until clean on-device test.',
            'The Laki IPTV app is not embedded into this image if it existed only in /data on the first box.'
        ],
    }
    dest_report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\nSUCCESS — FULL BOOTLOADER IMAGE PACKED AND OFFLINE VERIFIED (NOT FLASH TESTED)')
    print(dest)
    print('SHA256:', result['full_sha256'])
    print('REPORT:', dest_report)
    print('V4 and original V5 images and their staging folders were not changed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        print('\nSTOP: NO VALIDATED FULL IMAGE. ' + str(ex), file=sys.stderr)
        sys.exit(1)
