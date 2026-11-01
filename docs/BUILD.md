# Reproducible offline build (Windows + WSL 2)

This guide describes building firmware images locally, not flashing devices. The donor ROMs used for the hybrid are [X96 Max Plus — Plus 5](https://slimboxtv.ru/x96max-plus/) and [Magicsee N5 Max X3 — 152F](https://slimboxtv.ru/n5max-x3/), available through [slimBOXtv](https://slimboxtv.ru/). The repository contains build scripts and documentation, not prebuilt ROM images.

## Starting point

The V5 workflow assumes a **previously assembled, successfully tested V4** level-1 Amlogic image directory. It does **not** automatically download or construct the hybrid kernel/device tree/vendor components from scratch.

Expected files on the Windows host (examples):

```text
C:\LakiBox-Backup\
  LAKI-Hybrid-V4-NOBOOTLOADER-UNTESTED.img
  LakiHybrid-V4-NOBOOTLOADER\
    image.cfg
    DDR.USB
    aml_sdc_burn.UBOOT
    aml_sdc_burn.ini
    platform.conf
    _aml_dtb.PARTITION
    boot.PARTITION
    dtbo.PARTITION
    logo.PARTITION
    odm.PARTITION
    product.PARTITION
    recovery.PARTITION
    system.PARTITION
    vbmeta.PARTITION
    vendor.PARTITION
```

If you **do not** have this exact working V4, these scripts are not a one-click firmware maker. In particular, do not substitute an unrelated S905X3 image and disable integrity checks simply to make them run.

## Prerequisites

- Windows 10/11 with Python 3.9+ (`py -3 --version`).
- Ubuntu on WSL 2 (`wsl --status`); the warning that **WSL1 is unsupported** is not a blocker when Ubuntu is running on WSL2.
- `AmlImagePack.exe` from your own Amlogic toolchain. The tested local path was `C:\AmlogicKitchen\bin\windows\AmlImagePack.exe`.
- 7+ GiB free for V5; another 5+ GiB for FULL staging and verification.
- Original V4 hash must match the documented working image, unless you have separately verified a new input.

From PowerShell:

```powershell
wsl -e bash -lc "echo WSL_OK; uname -m"
wsl -u root -e bash -lc "apt update && apt install -y e2fsprogs android-sdk-libsparse-utils"
wsl -e bash -lc "command -v simg2img; command -v img2simg; command -v debugfs; command -v e2fsck"
```

All four utilities must resolve to executable paths. `wsl --status` alone does not confirm they are installed.

## V5 NOBOOTLOADER

Start in the repository root in **PowerShell or CMD**:

```powershell
py -3 scripts\finalize_laki_v5.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

What this does:

1. Confirms V4 input directory, the **known V4 IMG SHA-256**, file availability, and free space.
2. Copies `LakiHybrid-V4-NOBOOTLOADER` to `LakiHybrid-V5-FINAL`, leaving V4 intact.
3. Uses WSL to convert sparse `system.PARTITION` to raw ext4, writes `/etc/default-permissions/laki-bluetooth.xml` with `debugfs`, checks the stored XML and mode, runs `e2fsck`, converts back and verifies the sparse roundtrip.
4. Packs a new IMG with `AmlImagePack -r`.
5. Creates the destination verification directory; unpacks the IMG using `AmlImagePack -d`; compares partition payload hashes against staging.
6. Writes the build report.

Expected outputs:

```text
C:\LakiBox-Backup\LakiHybrid-V5-FINAL\
C:\LakiBox-Backup\LAKI-Hybrid-V5-FINAL-WiFi-BT.img
C:\LakiBox-Backup\LakiHybrid-V5-FINAL-VERIFY\
C:\LakiBox-Backup\LAKI-Hybrid-V5-FINAL-BUILD-REPORT.json
```

The USB Burning Tool pack/unpack roundtrip validates image **contents and format**, not boot functionality. The on-device effect of the default-permission XML after a clean installation has not yet been measured.

**Known historical issue:** the first version of `finalize_laki_v5.py` did not create the `LakiHybrid-V5-FINAL-VERIFY` folder before calling `AmlImagePack -d`; the operator manually created the folder, unpacked and SHA-256 compared all 12 components, and created the build report. The version committed here adds `CHECK.mkdir(parents=True, exist_ok=False)` before the unpack step. This code change has been syntax-checked but not independently end-to-end tested with the Windows firmware inputs.

## V5 FULL (X96 bootloader record)

Only proceed **after** the V5 NOBOOTLOADER image is fully verified and its JSON report exists.

```powershell
py -3 scripts\build_laki_v5_full.py --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe"
```

The FULL builder:

- Validates the NOBOOTLOADER V5 image SHA-256 against the report.
- Validates V5 stage file hashes from that report.
- Requires the **known X96 DDR and USB U-Boot pair** (hashes below).
- Adds one `[LIST_VERIFY]` manifest record mapping `DDR.USB` to `PARTITION/bootloader`.
- Packs a **separate** FULL image, unpacks it, compares source/unpacked payload hashes and checks the manifest entry.
- Preserves the original V4/V5 files.

Expected outputs:

```text
C:\LakiBox-Backup\LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img
C:\LakiBox-Backup\LAKI-Hybrid-V5-FULL-BUILD-REPORT.json
```

The X96 bootloader entry makes it **eligible** for programming when the burn tool requests bootloader flashing. It does not guarantee what a specific device/USB Burning Tool configuration will program.

## Reference hashes

```text
V4 working IMG:
D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF

V5 NOBOOTLOADER offline-verified IMG:
900DCEF88826BEC6F77516788B5612022C338515E945E309CC41EDCE1631CD4B

V5 FULL offline-verified IMG:
AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9

X96 DDR.USB:
77CB764B897F59D146178513CC3563EB1499A06F3DCCCB93A3F405C16F999D33

X96 aml_sdc_burn.UBOOT:
8BE0C10AF6D8FA087ABCEACD7F09D0AA16356B508EDE647E08CDE1E5A4ED0E45
```

On Windows:

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img' -Algorithm SHA256
```

If the hash differs, do not assume the image is the same one documented here. Validate provenance and every stage.

## Build errors

- `Missing ... image.cfg`: the required earlier V5 stage has not been created; build NOBOOTLOADER first.
- `Check WSL tools` fails: WSL may work while `simg2img`/`img2simg` are missing. Install `android-sdk-libsparse-utils`.
- `cannot open directory ... VERIFY`: the unpack destination must exist. The current scripts create it; older versions did not.
- `Output already exists`: safe-stop behavior. Do **not** remove directories unless you have checked their contents and retained backups. Prefer a new output location or archive completed stages.
- SHA mismatch: stop, locate the different source file, and do not use the resulting image.

The build scripts never execute a flashing operation or modify device partitions.
