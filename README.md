# Orion LAKI TV Box (S905X3) — Android TV hybrid firmware

**Community research and reproducible offline build tools for the Orion LAKI TV box, based on Amlogic S905X3 / AC213 and the Unisoc UWE5621 Wi-Fi/Bluetooth chipset.**

[**Srpski / Serbian README**](README.sr.md) · [Build guide](docs/BUILD.md) · [Hardware details](docs/HARDWARE.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Flashing and recovery risks](docs/FLASHING.md)

> [!IMPORTANT]
> **The working firmware is V4, tested on one physical box.** V5 NOBOOTLOADER and V5 FULL have been built and their contents verified offline, **but neither V5 image has been boot-tested or clean-install tested**. These tools do not flash hardware, and no firmware images or proprietary vendor binaries are included in this repository.

## Why this exists

The Orion LAKI TV box can boot some Amlogic S905X3 Android TV ROMs, but many of them do **not** support its **Unisoc UWE5621** Wi-Fi/Bluetooth hardware. A SlimBOXtv ATV 9.20 build for X96 Max Plus 5 booted and ran over Ethernet, yet Wi-Fi/BT did not work. Copying kernel modules from the stock ROM was insufficient because of kernel symbol/version incompatibilities. A Magicsee N5 Max X3-based ROM contained appropriate Unisoc kernel and user-space components, but the unmodified Magicsee firmware consistently failed flashing with `DiskInitial` at ~7%.

A hybrid image using the working X96 USB DDR/U-Boot components, an AC213-adjusted device tree, and the Magicsee kernel/system/vendor/Unisoc stack successfully flashed and booted.

## Tested hardware

| Item | Observed configuration |
| --- | --- |
| Product | Orion LAKI TV Box |
| SoC | Amlogic S905X3 (`sm1`) |
| Board | AC213; stock DT identifier `sm1_ac213_g10xc2g` |
| Hybrid DT identifier | `sm1_ac213_2g` |
| Memory | 2 GB RAM, 16 GB eMMC/storage |
| Wireless | Unisoc UWE5621 (SDIO Wi-Fi + Bluetooth) |
| Original software | Android 9 |
| Tested hybrid kernel | Linux 4.9.113, ARMv7 userspace/kernel |

**The name “LAKI” does not prove that another device has the same board revision, RAM/DDR configuration, eMMC, or wireless chip.** Check hardware before any flash. See [hardware identification](docs/HARDWARE.md).

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

## Releases and SHA-256 fingerprints

These are **checksums of files built on the tester's Windows PC**, not files hosted in this repository:

| Artifact | SHA-256 | Status |
| --- | --- | --- |
| V4 `LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img` | `D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF` | **Actually flashed and confirmed working**; historical filename says `UNTESTED` |
| V5 `LAKI-Hybrid-V5-FINAL-WiFi-BT.img` | `900DCEF88826BEC6F77516788B5612022C338515E945E309CC41EDCE1631CD4B` | Offline pack/unpack + partition hash validation only |
| V5 FULL `LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img` | `AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9` | Offline pack/unpack + partition hash validation only |

See [checksums and build provenance](docs/BUILD.md#reference-hashes) for the original X96 DDR/U-Boot fingerprints. **A matching hash proves identity, not compatibility with another board.**

## Build the V5 images on your own PC

Only build if you have **your own lawful copies** of the compatible ROM components and the previously prepared V4 unpacked staging directory. The scripts cannot reconstruct proprietary images from source code alone.

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

## Do **not** flash based on this README alone

There is **no universal safe USB Burning Tool checkbox combination** for every LAKI revision. In particular, enabling **Erase flash** or **Erase bootloader** can destroy data and/or recovery capability. The first physical box had already received the X96 bootloader in an earlier flash **before** the working V4 hybrid image was flashed. Therefore, the successful V4 test does **not** demonstrate that a V5 FULL image will initialize a second stock unit in one operation.

Read [docs/FLASHING.md](docs/FLASHING.md) before attempting any hardware operation. If you cannot verify the board and recoverability, **do not flash the FULL image**.

## Reporting results / helping others

Please open an issue with the [hardware report template](.github/ISSUE_TEMPLATE/hardware-report.md). Include exact DT ID, board markings, RAM/eMMC configuration where known, bootloader status, ROM revision, and **redacted** error logs. Do not post device serial numbers, public IP addresses, Wi-Fi passwords, Bluetooth MAC addresses, token files, activation keys, or DRM keys.

## Distribution and licensing

This repository provides only community-authored text, XML, and build scripts. **It does not contain or grant redistribution rights to proprietary Amlogic, Magicsee, SlimBOXtv, Orion/LAKI images, kernel binaries, bootloader binaries, APKs, or third-party packaging tools.** Do not upload such material to GitHub Releases without confirming distribution rights. The repository owner should choose and add a license for the original scripts/documentation separately; **no license is granted by default**.

This is a community experiment, **not an official Orion/SlimBOXtv/Magicsee project**. No warranty of compatibility or recovery.
