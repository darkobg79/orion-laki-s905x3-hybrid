#!/usr/bin/env python3
"""One-command, donor-IMG -> LAKI Hybrid V6 FULL AUDIO builder (offline only).

Inputs: EXACT X96 Max Plus 5 ATV 9.20 donor IMG and EXACT Magicsee N5 Max
X3 152F UWE5621 ATV 9.20 donor IMG. NO V4/V4.1/V5/V5.1 IMG needed.

This builder never flashes hardware, never downloads proprietary images, and
never overwrites its input files. It pins the historically verified firmware
components and refuses unexpected revisions. A specific V6 build was operator-reported 9/9 PASS on one previously modified LAKI; new builds and stock bootloaders are not validated by that result.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from patch_laki_earc import parse, patch
from patch_v4_partitions_offline import aml_entries, change_boot, get_prop, read_boot_second
from v6_wifi_patch import patch_multi_dtb, reassemble_boot, stable_gzip

# These fingerprints come from the 2026-10-31/11-01 ORIGINAL donor analysis,
# the V4 Wi-Fi/BT and V4.1 eARC patch verification. Not guessed filenames.
PIN = {
    'x96_ddr': '77CB764B897F59D146178513CC3563EB1499A06F3DCCCB93A3F405C16F999D33',
    'x96_uboot': '8BE0C10AF6D8FA087ABCEACD7F09D0AA16356B508EDE647E08CDE1E5A4ED0E45',
    'x96_aml_dtb': 'E449A73D83BD474D1E10E3BB05F006034E5CBC41AE16480AA22FDE395F981DB0',
    'magicsee_boot': '3805006439B9EE91F5743B26E0BA367C4D9D737129CF02305C5E3E6D5115AEAA',
    'magicsee_dtb': '7C9CAB1E576FAF78E98D428657E85A7F01F63889B64ED595275FDC331355C759',
    'magicsee_vendor': 'CF5454BDACE5398772CD8426799150F802DBD2D88E1F870707FCE39CC049E61D',
    'magicsee_manifest': '96DDF47E257F5D251CF4F2F23A9AB38E4EE26612528AFD38B9D341062E44BA3E',
    'wifi_dtb': '3839A4E481E5F2F8F418A146446F70C5F5586A4BB09E36FA9BB6A9C79F029518',
    'wifi_dtb_raw': '12F55E4A6C9D59BC150DE01A5878D052D8CC5BFBE6AD00CD009506B811614317',
    'wifi_boot': '223D1F4FCFF1677B019796543CD7A6AAAE4900E1FE48DEB91836E5EF9E7EAF61',
    'audio_dtb': 'FD33629D04630DF9A437DDDD5F870FE94D6C4EE9755055B5B380DADE625FC13E',
    'audio_dtb_raw': '948D1011765FEC7C73470EFC40C03758D1E340D47F6E70F635783E8C06CC9CD9',
    'audio_boot': 'A334E39C6600731A352A2DB259C1B0F6F4D24BA09EFB049BC357DF9F52E91F6B',
}
BOARD = b'sm1_ac213_2g\0'
EXPECTED_PARTITIONS = {
    '_aml_dtb.PARTITION','boot.PARTITION','dtbo.PARTITION','logo.PARTITION',
    'odm.PARTITION','product.PARTITION','recovery.PARTITION','system.PARTITION',
    'vbmeta.PARTITION','vendor.PARTITION'
}
SOURCE_FILES = EXPECTED_PARTITIONS | {'DDR.USB','aml_sdc_burn.UBOOT','aml_sdc_burn.ini','platform.conf','image.cfg'}
PAYLOAD_FILES = SOURCE_FILES - {'image.cfg'}  # AmlImagePack may rewrite manifest formatting on unpack
OUTPUT_IMG = 'LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img'
PARTITION_SIZE_LIMIT = 1342177280  # 1280 MiB, historical V5 raw system limit
MIN_FREE_GIB = 12

class BuildRefused(RuntimeError):
    pass

def stop(reason: str) -> None:
    raise BuildRefused(reason)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def sha256_file(path: Path) -> str:
    dig = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            dig.update(chunk)
    return dig.hexdigest().upper()

def pin_file(path: Path, key: str) -> str:
    actual = sha256_file(path)
    expected = PIN[key]
    if actual != expected:
        stop(f'Unexpected source {path.name}: SHA256 {actual} != known {expected}. '
             'Use the EXACT historical donor revision; do not bypass this check.')
    return actual

def command(args: list[str], label: str, cwd: Path | None = None) -> str:
    print('\n== ' + label + ' ==', flush=True)
    result = subprocess.run(args, cwd=str(cwd) if cwd else None,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors='replace', check=False)
    print(result.stdout[-16000:], flush=True)
    if result.returncode:
        stop(f'{label} failed (exit {result.returncode}). No verified V6 image exists.')
    return result.stdout

def check_full_manifest(blob: bytes) -> None:
    """Fail unless an explicit X96 DDR.USB PARTITION/bootloader entry exists once."""
    section, entries = '', []
    for line in blob.decode('latin1').splitlines():
        s = line.strip()
        if not s or s.startswith(('#',';')):
            continue
        if s.startswith('[') and s.endswith(']'):
            section = s.upper()
            continue
        if section in ('[LIST_NORMAL]', '[LIST_VERIFY]'):
            fields = dict(re.findall(r'([a-zA-Z_]+)\s*=\s*"([^"]+)"', s))
            if not all(k in fields for k in ('file','main_type','sub_type')):
                stop(f'Bad image.cfg entry: {s}')
            entries.append((section, fields['file'],fields['main_type'],fields['sub_type']))
    expected = ('[LIST_VERIFY]', 'DDR.USB', 'PARTITION', 'bootloader')
    if entries.count(expected) != 1:
        stop('FULL manifest must contain exactly one DDR.USB PARTITION/bootloader record')
    required = {('[LIST_NORMAL]', 'DDR.USB', 'USB','DDR'),
                ('[LIST_NORMAL]', 'DDR.USB', 'USB','UBOOT')}
    if not required.issubset(set(entries)):
        stop('Missing X96 USB DDR or UBOOT record in manifest')
    files = {file for _,file,_,_ in entries}
    if not EXPECTED_PARTITIONS.issubset(files):
        stop('Manifest lacks expected Android partitions')
    if len(entries) != len(set(entries)):
        stop('Duplicate manifest records detected')

def manifest_semantics(blob: bytes) -> list[tuple[str,str,str,str]]:
    sect, rows = '', []
    for line in blob.decode('latin1').splitlines():
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            sect = s.upper()
            continue
        if sect not in ('[LIST_NORMAL]','[LIST_VERIFY]') or not s or s.startswith(('#',';')):
            continue
        d = dict(re.findall(r'([a-zA-Z_]+)\s*=\s*"([^"]+)"', s))
        if not all(k in d for k in ('file','main_type','sub_type')):
            stop(f'Unrecognized image.cfg line: {s}')
        rows.append((sect,d['file'],d['main_type'],d['sub_type']))
    return sorted(rows)

def payload_hashes(folder: Path) -> dict[str,str]:
    return {p.name:sha256_file(p) for p in sorted(folder.iterdir())
            if p.is_file() and (p.name in PAYLOAD_FILES)}

def check_stage_contents(folder: Path) -> None:
    missing = sorted(SOURCE_FILES - {p.name for p in folder.iterdir() if p.is_file()})
    if missing:stop(f'Missing required source files under {folder}: {missing}')
    check_full_manifest((folder / 'image.cfg').read_bytes())

def verify_wifi_earc_patch(x96_dtb: bytes, magicsee_boot: bytes) -> tuple[bytes, bytes, dict]:
    """Reconstruct exactly V4 Wi-Fi/BT + V4.1 eARC from ORIGINAL donor blobs.

    The resulting partition SHA256s are pinned against reference V4.1 audio
    blobs tested offline in the original development, not baked-in binaries.
    """
    wifi_dtb, entries, replaced = patch_multi_dtb(x96_dtb)
    wifi_raw = gzip.decompress(wifi_dtb)
    if sha256_bytes(wifi_raw) != PIN['wifi_dtb_raw']:
        stop('Wi-Fi/BT DTB content differs from verified V4: '
             f'actual uncompressed SHA256={sha256_bytes(wifi_raw)}; '
             f'expected={PIN["wifi_dtb_raw"]}. STOP, do not flash.')
    if sha256_bytes(wifi_dtb) != PIN['wifi_dtb']:
        stop('Wi-Fi/BT canonical gzip differs from verified V4: '
             f'actual compressed SHA256={sha256_bytes(wifi_dtb)}; '
             f'expected={PIN["wifi_dtb"]}; header={wifi_dtb[:10].hex()}. '
             'No verification was bypassed.')
    wifi_boot = reassemble_boot(magicsee_boot, wifi_dtb)
    if sha256_bytes(wifi_boot) != PIN['wifi_boot']:
        stop('Reconstructed original V4 boot does not match golden hash')

    raw = gzip.decompress(wifi_dtb)
    spans = aml_entries(raw)
    if len(spans) != 4 or replaced != [2]:
        stop('Unexpected AC213 board index or multi-DTB table')
    found = []
    updated = bytearray(raw)
    for index,off,length in spans:
        fdt_total = int.from_bytes(raw[off+4:off+8], 'big')
        if not (40 <= fdt_total <= length):stop('Invalid DTB length in slot')
        fdt,tail = raw[off:off+fdt_total],raw[off+fdt_total:off+length]
        tree = parse(fdt)
        if get_prop(tree,'/','amlogic-dt-id') != BOARD:
            continue
        if index != 2:stop('AC213_2g appeared at an unexpected index')
        # Precise wiring invariant from Orion original and proven V4 hybrid.
        if get_prop(tree,'/wifi','interrupt_pin') != bytes.fromhex('000000190000005400000000'):
            stop('LAKI AC213 Wi-Fi IRQ pin does not match tested V4')
        if get_prop(tree,'/wifi','irq_trigger_type') != b'GPIO_IRQ_HIGH\0':
            stop('LAKI AC213 Wi-Fi IRQ polarity mismatch')
        if get_prop(tree,'/bt-dev','gpio_reset') != bytes.fromhex('000000190000005300000000'):
            stop('LAKI AC213 Bluetooth GPIO mismatch')
        if get_prop(tree,'/bt-dev','gpio_en') is not None:
            stop('Old X96 bluetooth gpio_en is still present')
        patched,notes = patch(fdt)
        if len(patched) != len(fdt):stop('eARC patch unexpectedly resized DTB')
        after = parse(patched)
        if get_prop(after,'/soc/bus@ff663000/earc@0','status') != b'disabled\0':
            stop('eARC was not disabled')
        if '/auge_sound/aml-audio-card,dai-link@6' in after['nodes']:
            stop('eARC DAI link remains present')
        updated[off:off+length] = patched+tail
        found.append({'index':index,'earc_notes':notes})
    if len(found) != 1:stop(f'Expected one sm1_ac213_2g variant; found {len(found)}')
    audio_dtb = stable_gzip(bytes(updated))
    audio_boot = change_boot(wifi_boot, wifi_dtb, audio_dtb)
    if sha256_bytes(gzip.decompress(audio_dtb)) != PIN['audio_dtb_raw']:
        stop('eARC audio DTB content differs from verified V4.1: '
             f'actual raw SHA256={sha256_bytes(gzip.decompress(audio_dtb))}; '
             f'expected={PIN["audio_dtb_raw"]}. STOP.')
    if sha256_bytes(audio_dtb) != PIN['audio_dtb']:
        stop('eARC audio DTB compressed hash differs from verified V4.1: '
             f'actual={sha256_bytes(audio_dtb)}; '
             f'expected={PIN["audio_dtb"]}; header={audio_dtb[:10].hex()}. STOP.')
    if sha256_bytes(audio_boot) != PIN['audio_boot']:
        stop('Final eARC-off boot.PARTITION differs from reference V4.1')
    if gzip.decompress(read_boot_second(audio_boot)[5]) != gzip.decompress(audio_dtb):
        stop('boot embedded second-stage DTB differs from _aml_dtb.PARTITION')
    final_raw = gzip.decompress(audio_dtb)
    for idx,off,length in spans:
        if idx != 2 and final_raw[off:off+length] != raw[off:off+length]:
            stop('A different board variant was modified!')
    return audio_boot,audio_dtb,{'target_board':'sm1_ac213_2g','target_index':2,
        'x96_dtb_sha256':sha256_bytes(x96_dtb),
        'v4_wifi_dtb_sha256':sha256_bytes(wifi_dtb),
        'v4_wifi_boot_sha256':sha256_bytes(wifi_boot),
        'v6_audio_dtb_sha256':sha256_bytes(audio_dtb),
        'v6_audio_boot_sha256':sha256_bytes(audio_boot),
        'other_board_slots_preserved':True,'earc_disabled':True,
        'earc_dai_link_removed':True,'magicsee_kernel_unchanged':True}

def wsl_path(win: Path) -> str:
    result = command(['wsl.exe','-e','wslpath','-a','-u',str(win)], 'Resolve WSL path')
    lines = [x.strip() for x in result.splitlines() if x.strip()]
    if not lines or not lines[-1].startswith('/'):
        stop(f'Cannot translate Windows path to WSL: {win}')
    return lines[-1]

def apply_system_customizations(system_file: Path, output_root: Path, scripts: Path) -> dict:
    """One pass: Android BT default permission + identity-only build.prop patch.

    Exactly one system.PARTITION staging copy changes, original donor files are
    read-only. The shell helper preserves donor build.prop ownership, mode and
    SELinux context, including known 0600 root:root input mode.
    """
    xml = scripts / 'laki-bluetooth-default-permissions.xml'
    sh = scripts / 'patch_v6_system_identity.sh'
    prop_helper = scripts / 'patch_android_properties_v6.py'
    if not all(p.is_file() for p in (xml,sh,prop_helper)):
        stop('Missing Bluetooth XML or system/identity patch helpers')
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml).getroot()
    if tree.tag != 'exceptions' or len(tree) != 1 or tree[0].attrib.get('package') != 'com.android.bluetooth':
        stop('Unexpected Android Bluetooth permission XML')
    old = sha256_file(system_file)
    command(['wsl.exe','-e','bash',wsl_path(sh),wsl_path(system_file),wsl_path(xml),
             wsl_path(output_root/'SYS-PATCH-WORK'),str(PARTITION_SIZE_LIMIT),
             wsl_path(prop_helper)],
            'Patch Bluetooth permission and Android identity in staged system.PARTITION')
    new = sha256_file(system_file)
    if old == new:stop('Android system.PARTITION was not modified')
    from patch_android_properties_v6 import CHANGES
    return {'original_magicsee_system_sha256':old,'patched_v6_system_sha256':new,
            'bluetooth_default_permission_added':True,
            'identity_properties':CHANGES,
            'source_build_prop_owner_preserved':True,
            'source_build_prop_mode_preserved_including_0600':True,
            'source_build_prop_selinux_context_preserved':True,
            'system_patch_passes':1}

def file_set_equal(stage: Path, verify: Path) -> dict[str,str]:
    a,b=payload_hashes(stage),payload_hashes(verify)
    if set(a) != set(b):stop(f'Pack/unpack file-list mismatch: {set(a)^set(b)}')
    if len(a) < 14:stop(f'Too few files verified: {len(a)}')
    for name in a:
        if a[name] != b[name]:stop(f'Pack/unpack SHA-256 mismatch for {name}')
    if manifest_semantics((stage/'image.cfg').read_bytes()) != manifest_semantics((verify/'image.cfg').read_bytes()):
        stop('Manifest entries changed during pack/unpack')
    check_full_manifest((verify/'image.cfg').read_bytes())
    return a

def prerequisites(x96_img: Path, magic_img: Path, packer: Path, output_dir: Path,
                  scripts: Path, require_wsl=True) -> dict:
    if output_dir.exists():stop(f'Output directory already exists (never overwrite): {output_dir}')
    for path in (x96_img,magic_img,packer, scripts/'patch_v6_system_identity.sh',
                 scripts/'laki-bluetooth-default-permissions.xml',
                 scripts/'patch_android_properties_v6.py'):
        if not path.is_file():stop(f'Missing required file: {path}')
    if x96_img.resolve() == magic_img.resolve():stop('X96 and Magicsee IMG cannot be identical')
    if x96_img.stat().st_size < 300*1024**2 or magic_img.stat().st_size < 300*1024**2:
        stop('Donor IMG files are unexpectedly small; do not build')
    # Never work under a source image directory; prevent inadvertent deletion on cleanup.
    if any(img == output_dir or img in output_dir.parents or output_dir in img.parents
           for img in (x96_img,magic_img)):
        stop('Output folder must not contain source IMG or vice versa')
    if not output_dir.parent.is_dir():
        stop(f'Output parent folder does not exist: {output_dir.parent}')
    free = shutil.disk_usage(output_dir.parent).free
    if free < MIN_FREE_GIB * 1024**3:
        stop(f'At least {MIN_FREE_GIB} GiB free is required for safe unpack, ext4 patch and repack; '
             f'found {free/(1024**3):.2f} GiB')
    if require_wsl:
        if os.name != 'nt':stop('Run on Windows 10/11 with WSL2; not native Linux')
        command(['wsl.exe','-e','bash','-lc',
                 'command -v simg2img && command -v img2simg && command -v debugfs && command -v e2fsck && command -v python3'],
                'Check WSL2 sparse/ext4 utilities')
    return {'x96_img_sha256':sha256_file(x96_img),
            'magicsee_img_sha256':sha256_file(magic_img),
            'free_gib':round(free/(1024**3),2)}

def build(x96_img: Path, magic_img: Path, packer: Path, output_root: Path,
          scripts: Path, *, check_only=False, keep_work=False) -> dict:
    pre = prerequisites(x96_img,magic_img,packer,output_root,scripts)
    print('\n== PRE-FLIGHT ==\n' + json.dumps(pre,indent=2),flush=True)
    if check_only:
        print('PREFLIGHT PASSED — read-only. Actual donor PARTITION identity is checked after unpacking during full build. No output created.')
        return pre
    output_root.mkdir(parents=False, exist_ok=False)
    failure_marker = output_root/'INCOMPLETE-NOT-VALIDATED.txt'
    failure_marker.write_text('Build incomplete or validation in progress. DO NOT FLASH.\n',encoding='utf-8')
    x96 = output_root/'X96-unpacked'
    magic = output_root/'Magicsee-unpacked'
    stage = output_root/'V6-internal-staging'
    verify = output_root/'V6-internal-verification'
    for folder in (x96,magic,verify):folder.mkdir()
    output_img = output_root/OUTPUT_IMG
    packer_cwd = packer.parent

    command([str(packer),'-d',str(x96_img),str(x96)],'Unpack original X96 donor IMG',packer_cwd)
    command([str(packer),'-d',str(magic_img),str(magic)],'Unpack original Magicsee donor IMG',packer_cwd)
    for folder in (x96,magic):check_stage_contents(folder)

    # Strictly match original research donor revisions instead of guessing.
    x96_pins = {name:pin_file(x96/name,key) for name,key in [
        ('DDR.USB','x96_ddr'),('aml_sdc_burn.UBOOT','x96_uboot'),
        ('_aml_dtb.PARTITION','x96_aml_dtb')]}
    magic_pins = {name:pin_file(magic/name,key) for name,key in [
        ('boot.PARTITION','magicsee_boot'),('_aml_dtb.PARTITION','magicsee_dtb'),
        ('vendor.PARTITION','magicsee_vendor'),('image.cfg','magicsee_manifest')]}
    ddr = (x96/'DDR.USB').read_bytes()
    uboot = (x96/'aml_sdc_burn.UBOOT').read_bytes()
    if len(uboot) != len(ddr)+512 or uboot[512:] != ddr:
        stop('X96 DDR/USB U-Boot pair does not match')
    if (x96/'image.cfg').read_bytes() != (magic/'image.cfg').read_bytes():
        stop('Original donor manifests differ; cannot safely merge these revisions')

    audio_boot,audio_dtb,audio_report = verify_wifi_earc_patch(
        (x96/'_aml_dtb.PARTITION').read_bytes(), (magic/'boot.PARTITION').read_bytes())

    # Crucial source choice: MAGICSEE SYSTEM, VENDOR AND OTHER ANDROID PARTITIONS.
    # Earlier experimental stage based on X96 system lacked working BT framework.
    shutil.copytree(magic,stage)
    for name in ('DDR.USB','aml_sdc_burn.UBOOT','aml_sdc_burn.ini','platform.conf','image.cfg'):
        shutil.copy2(x96/name,stage/name)
    (stage/'boot.PARTITION').write_bytes(audio_boot)
    (stage/'_aml_dtb.PARTITION').write_bytes(audio_dtb)
    check_stage_contents(stage)

    # Verify no Android partition other than target boot/dtb/system was changed.
    from_magic = payload_hashes(magic)
    from_x96 = payload_hashes(x96)
    before_perm = payload_hashes(stage)
    for name,hashval in from_magic.items():
        if name in {'boot.PARTITION','_aml_dtb.PARTITION','DDR.USB','aml_sdc_burn.UBOOT','aml_sdc_burn.ini','platform.conf','image.cfg'}:
            continue
        if before_perm.get(name) != hashval:
            stop(f'Unexpected change to Magicsee Android partition {name}')
    for name in ('DDR.USB','aml_sdc_burn.UBOOT','aml_sdc_burn.ini','platform.conf'):
        if before_perm[name] != from_x96[name]:stop(f'X96 burn component mismatch: {name}')
    if (stage/'image.cfg').read_bytes() != (x96/'image.cfg').read_bytes():
        stop('X96 image.cfg was changed unexpectedly')
    bt_report=apply_system_customizations(stage/'system.PARTITION',output_root,scripts)
    after_perm=payload_hashes(stage)
    for name,value in before_perm.items():
        if name != 'system.PARTITION' and after_perm.get(name) != value:
            stop(f'Unexpected modification outside system.PARTITION: {name}')
    if sha256_file(stage/'boot.PARTITION') != PIN['audio_boot']:
        stop('Known audio boot SHA-256 was unexpectedly changed')
    if sha256_file(stage/'_aml_dtb.PARTITION') != PIN['audio_dtb']:
        stop('Known audio DTB SHA-256 was unexpectedly changed')

    command([str(packer),'-r',str(stage/'image.cfg'),str(stage),str(output_img)],
            'Pack single LAKI V6 FULL AUDIO IMG',packer_cwd)
    if not output_img.is_file() or output_img.stat().st_size < 300*1024**2:
        stop('V6 IMG missing or suspiciously small')
    unpacked_img = verify
    command([str(packer),'-d',str(output_img),str(unpacked_img)],
            'Unpack V6 IMG for independent payload verification',packer_cwd)
    verified=file_set_equal(stage,verify)
    for name,hashval in verified.items():
        if name not in {'system.PARTITION','boot.PARTITION','_aml_dtb.PARTITION','DDR.USB','aml_sdc_burn.UBOOT','aml_sdc_burn.ini','platform.conf','image.cfg'}:
            if hashval != from_magic[name]:stop(f'Final {name} differs from Magicsee donor unexpectedly')
    # Read source files once more so any concurrent modification is detected.
    if sha256_file(x96_img) != pre['x96_img_sha256'] or sha256_file(magic_img) != pre['magicsee_img_sha256']:
        stop('Donor IMG changed during build; result untrusted')

    report = {
        'version':'6.0.0',
        'status':'PACKED AND OFFLINE-VERIFIED; NO V6 HARDWARE TEST; STOCK BOOTLOADER UNTESTED',
        'utc_created':datetime.now(timezone.utc).isoformat(),
        'hardware_model':'Orion LAKI M6CW4K SM1/AC213 2GB/16GB Unisoc UWE5621',
        'android_model':'m6cw4k',
        'firmware_display_id':'LAKI Hybrid V6 FULL AUDIO by DarkoBG',
        'output_image':str(output_img),
        'output_sha256':sha256_file(output_img),
        'output_bytes':output_img.stat().st_size,
        'x96_donor_img':str(x96_img),'x96_donor_sha256':pre['x96_img_sha256'],
        'magicsee_donor_img':str(magic_img),'magicsee_donor_sha256':pre['magicsee_img_sha256'],
        'verified_x96_parts':x96_pins,
        'verified_magicsee_parts':magic_pins,
        'device_tree_changes':audio_report,
        'system_changes':bt_report,
        'verified_img_payload_sha256':verified,
        'full_bootloader_record_present':True,
        'input_images_unchanged':True,
        'firmware_sources':'X96 USB DDR/U-Boot + X96 AC213 DTB (WiFi/BT/eARC patched) + Magicsee kernel/Android partitions',
        'warnings':[
            'FULL includes X96 PARTITION/bootloader; untested on factory-stock Orion bootloader.',
            'V6 has not been physically flashed; offline checks are NOT evidence it will boot.',
            'V6 READ_CONTACTS default-permission behavior after clean flash is untested.',
            'Android Settings may use application-specific labels; verify displayed model/build after flash.',
            'Video, AUX, Wi-Fi and BT were verified on prior V5.1 FULL AUDIO, NOT on this V6 image.',
            'Operator-specific IPTV apps, DRM/keys or private /data are not included.',
            'Rights to redistribute proprietary assembled IMG are not granted by this tool.',
        ],
    }
    (output_root/'LAKI-V6-BUILD-REPORT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (output_root/'SHA256SUMS.txt').write_text(f"{report['output_sha256']}  {OUTPUT_IMG}\n",encoding='utf-8')
    failure_marker.unlink()
    if not keep_work:
        # Only remove directories created by this invocation, never input folders.
        for folder in (x96,magic,stage,verify,output_root/'SYS-PATCH-WORK'):
            if folder.exists():shutil.rmtree(folder)
    print('\n'+'='*72)
    print('SUCCESS: V6 FULL AUDIO packed and OFFLINE verified (not hardware-tested)')
    print('Image:',output_img)
    print('SHA256:',report['output_sha256'])
    print('Report:',output_root/'LAKI-V6-BUILD-REPORT.json')
    print('No V4, V4.1, V5 or V5.1 intermediate input was used.')
    return report

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--x96-img',type=Path,required=True,help='Original X96 Max Plus 5 ATV 9.20 IMG')
    p.add_argument('--magicsee-img',type=Path,required=True,help='Original Magicsee N5 Max X3 152F ATV 9.20 IMG')
    p.add_argument('--packer',type=Path,default=Path(r'C:\AmlogicKitchen\bin\windows\AmlImagePack.exe'))
    p.add_argument('--output-root',type=Path,required=True,help='NEW output directory (must not exist)')
    p.add_argument('--check-only',action='store_true',help='No-write input/tool/free-space check')
    p.add_argument('--keep-work',action='store_true',help='Keep internal unpacked/staging dirs for audit (large)')
    a=p.parse_args()
    if os.name != 'nt':stop('This builder is for Windows CMD/PowerShell with WSL2')
    build(a.x96_img.resolve(),a.magicsee_img.resolve(),a.packer.resolve(),
          a.output_root.resolve(),Path(__file__).resolve().parent,
          check_only=a.check_only,keep_work=a.keep_work)

if __name__=='__main__':
    try:main()
    except (BuildRefused,ValueError,FileNotFoundError,subprocess.SubprocessError,PermissionError) as exc:
        print('\nSTOP — NO VERIFIED V6 IMAGE: '+str(exc),file=sys.stderr)
        sys.exit(1)
