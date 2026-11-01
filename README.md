# Orion LAKI M6CW4K TV Box (S905X3) — Android TV Hybrid Firmware

**Technical documentation and offline V5 build tools for the Orion LAKI M6CW4K TV box (Amlogic S905X3 / AC213, Unisoc UWE5621 Wi-Fi/Bluetooth). The original V5 tools start from a prepared V4 image; the V5.1 builder uses local V5 FULL and V4.1 audio images.**

[**Srpski / Serbian README**](README.sr.md) · [**Start Here / Beginner build guide**](docs/START_HERE.md) · [**Srpski: Počni ovde**](docs/START_HERE.sr.md) · [V4.1 audio validation](docs/V4_1_AUDIO.md) · [V5.1 FULL AUDIO](docs/V5_1_FULL_AUDIO.md) · [Build guide](docs/BUILD.md) · [Hardware details](docs/HARDWARE.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Flashing and recovery risks](docs/FLASHING.md)

> [!IMPORTANT]
> **V4.1 is the latest version physically tested on one box (IPTV picture, Wi-Fi, Bluetooth audio and analog AUX).** V4 had Wi-Fi/BT success but an audio-card/IPTV-video failure. V5 NOBOOTLOADER and V5 FULL have been built and their contents verified offline, **but neither V5 image has been boot-tested or clean-install tested**. These tools do not flash hardware, and no firmware images or proprietary vendor binaries are included in this repository.

## Why this exists

The Orion LAKI TV box can boot some Amlogic S905X3 Android TV ROMs, but many of them do **not** support its **Unisoc UWE5621** Wi-Fi/Bluetooth hardware. A SlimBOXtv ATV 9.20 build for X96 Max Plus 5 booted and ran over Ethernet, yet Wi-Fi/BT did not work. Copying kernel modules from the stock ROM was insufficient because of kernel symbol/version incompatibilities. A Magicsee N5 Max X3-based ROM contained appropriate Unisoc kernel and user-space components, but the unmodified Magicsee firmware consistently failed flashing with `DiskInitial` at ~7%.

A hybrid image using the working X96 USB DDR/U-Boot components, an AC213-adjusted device tree, and the Magicsee kernel/system/vendor/Unisoc stack successfully flashed and booted.

## Firmware sources and local image filenames

The donor firmware was selected from the **slimBOXtv 9.20 ATV** releases for these specific device revisions:

| Donor firmware | Verified revision on the project site | Project download page | Role in the hybrid |
| --- | --- | --- | --- |
| X96 Max Plus | **Plus 5** | [slimBOXtv — X96Max Plus](https://slimboxtv.ru/x96max-plus/) | Working DDR/USB U-Boot components |
| Magicsee N5 Max X3 | **152F**, Unisoc UWE5621DS | [slimBOXtv — N5 Max X3](https://slimboxtv.ru/n5max-x3/) | Kernel, Android userspace, and wireless stack |

**Select the exact revision on each project page.** The original downloaded archive/IMG filenames have not been independently confirmed; do not rely on guessed filenames. The unmodified Magicsee image failed at approximately 7% with `Uboot/Get result/DiskInitial error`. The X96 image booted but lacked functional Wi-Fi and Bluetooth on the tested LAKI box.

### Locally built LAKI Hybrid images

| IMG filename | Validation status |
| --- | --- |
| `LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img` | Physically flashed and tested: Android boots; Wi-Fi and Bluetooth speaker audio work (Bluetooth required a manual permission grant) |
| `LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img` | **Physically flashed on one box:** IPTV video and AUX audio work; Bluetooth audio and Wi-Fi work. V4.1 packed IMG hash not published. |
| `LAKI-Hybrid-V5-FINAL-WiFi-BT.img` | Packed and SHA-256 verified offline; **not flash-tested** |
| `LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img` | Packed and SHA-256 verified offline; **not flash-tested** |

These three names identify local build outputs, **not downloadable ROMs in this repository**. The V5 scripts require an already prepared V4 image; they do not construct V4 from the donor firmware automatically.

## Tested hardware

| Item | Observed configuration |
| --- | --- |
| Product | Orion LAKI TV Box (M6CW4K) |
| SoC | Amlogic S905X3 (`sm1`) |
| Board | AC213; stock DT identifier `sm1_ac213_g10xc2g` |
| Hybrid DT identifier | `sm1_ac213_2g` |
| Memory | 2 GB RAM, 16 GB eMMC/storage |
| Wireless | Unisoc UWE5621 (SDIO Wi-Fi + Bluetooth) |
| Original software | Android 9 |
| Tested hybrid kernel | Linux 4.9.113, ARMv7 userspace/kernel |

**The name “LAKI” does not prove that another device has the same board revision, RAM/DDR configuration, eMMC, or wireless chip.** Check hardware before any flash. See [hardware identification](docs/HARDWARE.md).

## V4.1: IPTV video and analog AUX sound verified on-device

V4 registered no ALSA sound card, and IPTV video could freeze after audio initialization failed. The **V4.1 eARC/DAI-link adjustment** restored the `AML-AUGESOUND` sound card and normal IPTV picture. Direct playback through TDM-B/T9015 produced an audible analog AV/AUX tone; Android IPTV audio also became audible after raising **STREAM_MUSIC from 17/65** (50/65 and 55/65 were tested). No GPIO inversion or HAL binary modification was required. An ONTEN HDMI switch changed HPD/video mode, but AUX loudness became equal when Android media volume was fixed at 50/65 in both positions. **Do not infer that HPD itself changed gain.** Full evidence and safe ADB tests: [V4.1 audio validation](docs/V4_1_AUDIO.md).

The V4.1 image was repacked/checked locally and physically tested, but its complete IMG SHA-256 has **not** been recorded in this repository. Existing V5 build scripts still start from the earlier V4 and **do not include the V4.1 audio fix**. The V5 images remain **offline-only validated**.

## What has actually been confirmed?

| Capability | V4 on physical box | V5 NOBOOTLOADER | V5 FULL |
| --- | --- | --- | --- |
| Amlogic USB Burning Tool packaging | ✅ | ✅ offline | ✅ offline |
| Boot into Android TV | ✅ | Not tested | Not tested |
| Wi-Fi network scan and connection | ✅ | Not tested | Not tested |
| Unisoc modules load | ✅ | Not tested | Not tested |
| Bluetooth enabled | ✅ after ADB permission grant | Not tested | Not tested |
| Bluetooth device discovery | ✅ | Not tested | Not tested |
| Pairing and Bluetooth speaker audio | ✅ | Not tested | Not tested |
| Fresh-install Bluetooth default permission | N/A; manual grant | Unverified on device | Unverified on device |
| First-time flashing on a stock LAKI box | Not tested as a single-step V4 flash | Not tested | **Not tested; high bootloader risk** |

### Confirmed Bluetooth fix on the running V4 box

The `com.android.bluetooth` process restarted hundreds of times. The `logcat -b crash` output identified the specific problem:

```text
Process: com.android.bluetooth
java.lang.SecurityException: Permission Denial ...
requires android.permission.READ_CONTACTS or android.permission.WRITE_CONTACTS
at com.android.bluetooth.pbap.BluetoothPbapService.start(...)
```

On this **already-rooted test box**, granting the missing runtime permission fixed the crash loop:

```bat
adb shell pm grant com.android.bluetooth android.permission.READ_CONTACTS
adb shell "dumpsys package com.android.bluetooth | grep -A 3 READ_CONTACTS"
adb shell "dumpsys bluetooth_manager | head -n 7"
```

Afterwards the adapter remained `ON`, discovered nearby Bluetooth devices, paired with a Xiaomi Desktop Speaker, and played sound. This is a **device/ROM-specific diagnosis**, not a universal cure for Bluetooth failures.

V5 adds an Android 9 default-permission XML to the system partition, intending to grant the same permission on a clean installation. **Whether that happens reliably on the physical box after a full erase/factory reset remains untested.**

## Hybrid architecture

| Component | Source/approach |
| --- | --- |
| USB DDR initialization / U-Boot components | Previously successful X96 Max Plus 5 ROM |
| Kernel (`boot`) | Magicsee N5 Max X3 firmware, Linux 4.9.113 |
| Device tree | AC213 2 GB adaptation; wireless IRQ and Bluetooth control adjusted |
| System / vendor / product / odm | Compatible Magicsee/SlimBOXtv ATV 9.20 components |
| Wi-Fi modules | `uwe5621_bsp_sdio`, `sprdwl_ng` |
| Bluetooth module | `sprdbt_tty` |
| Bluetooth HAL and Android app | Magicsee firmware |
| V5 system-only patch | `READ_CONTACTS` default-permission exception |
| V5 FULL change | Explicit `PARTITION/bootloader` record using **X96** DDR source, **not** the failing Magicsee bootloader |

The V4 `NOBOOTLOADER` package **still contains USB DDR and burn-time U-Boot components**. “NOBOOTLOADER” means it omits the *explicit bootloader partition entry in the manifest*, **not** that the flasher can never modify a bootloader. Actual flashing behavior also depends on USB Burning Tool settings.

## Local images and SHA-256 fingerprints

**V4.1:** `LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img` was physically tested, but its SHA-256 is not included here. Never substitute the V4 SHA-256 below for V4.1.

These are **checksums of files built on the tester's Windows PC**, not files hosted in this repository:

| Artifact | SHA-256 | Status |
| --- | --- | --- |
| V4 `LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img` | `D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF` | **Actually flashed and confirmed working**; historical filename says `UNTESTED` |
| V5 `LAKI-Hybrid-V5-FINAL-WiFi-BT.img` | `900DCEF88826BEC6F77516788B5612022C338515E945E309CC41EDCE1631CD4B` | Offline pack/unpack + partition hash validation only |
| V5 FULL `LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img` | `AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9` | Offline pack/unpack + partition hash validation only |

See [checksums and build provenance](docs/BUILD.md#reference-hashes) for the original X96 DDR/U-Boot fingerprints. **A matching hash proves identity, not compatibility with another board.**

## Build the V5 images on your own PC

Building V5 requires a previously assembled and tested V4 firmware directory. The original donor ROMs are available from [slimBOXtv](https://slimboxtv.ru/): [X96 Max Plus — Plus 5 revision](https://slimboxtv.ru/x96max-plus/) and [Magicsee N5 Max X3 — 152F revision with Unisoc UWE5621](https://slimboxtv.ru/n5max-x3/). The V5 scripts do not assemble the V4 hybrid from scratch.

Prerequisites:

- Windows with Python 3.9+, WSL 2 Ubuntu, and `AmlImagePack.exe` obtained separately.
- WSL utilities: `e2fsprogs` and `android-sdk-libsparse-utils`.
- Working V4 files stored in `C:\LakiBox-Backup` (names and layout documented in [BUILD.md](docs/BUILD.md)).
- Free disk space for large ext4 and sparse-image staging files.

```powershell
wsl -u root -e bash -lc "apt update && apt install -y e2fsprogs android-sdk-libsparse-utils"
wsl -e bash -lc "command -v simg2img; command -v img2simg; command -v debugfs; command -v e2fsck"
py -3 scripts\finalize_laki_v5.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

**After successful offline validation of the V5 NOBOOTLOADER image and build report**, the separate FULL variant is built using:

```powershell
py -3 scripts\build_laki_v5_full.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

The build scripts never connect to ADB, never flash a device, and are intended to leave the V4 input unchanged. The V5 finalizer in this repository includes the fix to create its verification directory before unpacking; **this revised script has not been re-run end-to-end in this environment**. The V5 files listed above were validated through the tester's completed pack/unpack and SHA-256 checks.

Full instructions, checks, and errors: [docs/BUILD.md](docs/BUILD.md).

## V5.1 FULL AUDIO — offline verified, not boot-tested

On 2026-11-01 a new V5.1 FULL AUDIO image was built using the physical-device-tested V4.1 `boot.PARTITION` and `_aml_dtb.PARTITION` in the original V5 FULL X96 image. Only those two payloads changed; `system`, `vendor` and the FULL X96 bootloader entry remained unchanged. The packed IMG was unpacked and SHA-256 verified offline, and Windows `Get-FileHash` independently confirmed the packed-image hash:

`B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378`

**V5.1 has NOT been flash-tested or stock-bootloader-tested.** The reproducible builder and verification guidance are in [V5.1 FULL AUDIO](docs/V5_1_FULL_AUDIO.md); there are no prebuilt images in this repository.

## Do **not** flash based on this README alone

There is **no universal safe USB Burning Tool checkbox combination** for every LAKI revision. In particular, enabling **Erase flash** or **Erase bootloader** can destroy data and/or recovery capability. The first physical box had already received the X96 bootloader in an earlier flash **before** the working V4 hybrid image was flashed. Therefore, the successful V4 test does **not** demonstrate that a V5 FULL image will initialize a second stock unit in one operation.

Read [docs/FLASHING.md](docs/FLASHING.md) before attempting any hardware operation. If you cannot verify the board and recoverability, **do not flash the FULL image**.

## Reporting results / helping others

Please open an issue with the [hardware report template](.github/ISSUE_TEMPLATE/hardware-report.md). Include exact DT ID, board markings, RAM/eMMC configuration where known, bootloader status, ROM revision, and **redacted** error logs. Do not post device serial numbers, public IP addresses, Wi-Fi passwords, Bluetooth MAC addresses, token files, activation keys, or DRM keys.

## Distribution and licensing

This repository contains documentation, configuration files, and build scripts for the LAKI Hybrid firmware project. Prebuilt firmware images are not included. The published scripts build V5 from an existing V4 hybrid image and do not create V4 from the donor ROMs.

The original scripts and documentation are available under the [MIT License](LICENSE). This is an independent community project focused on experimentation, knowledge sharing, and further development of firmware for the Orion LAKI TV Box.

This is a community experiment, **not an official Orion/SlimBOXtv/Magicsee project**. No warranty of compatibility or recovery.
