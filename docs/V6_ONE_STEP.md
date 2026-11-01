# LAKI Hybrid V6 FULL AUDIO by DarkoBG — single-step build from two donor ROMs

**V6 needs no V4, V4.1, V5 or V5.1 image or intermediate staging folder.** Users supply two original donor `.img` files, and one command performs unpacking, patching, packing and validation. Temporary build stages are internal and removed on a successful build.

> [!CAUTION]
> **A specific V6 IMG was successfully built end-to-end on Windows, independently SHA-256 checked, and operator-reported to pass 9/9 physical tests on one previously modified LAKI device (2026-11-01).** The output is **FULL** with an explicit X96 bootloader record. Do not assume compatibility with a factory-stock LAKI or a different board. See [FLASHING.md](FLASHING.md).

## Hardware scope

Orion LAKI M6CW4K, Amlogic S905X3/SM1, AC213 board, 2 GB RAM/16 GB flash, Unisoc UWE5621. Board markings and DDR configuration must match; a matching commercial product name is not sufficient.

## Downloads (obtained by the user, not bundled here)

1. **X96 Max Plus → Plus 5 revision → slimBOXtv 9.20 ATV**: https://slimboxtv.ru/x96max-plus/ . Locate the *Plus 5* subsection, not Plus 100, Plus 2101, etc.
2. **Magicsee N5 Max X3 → 152F with Unisoc UWE5621DS → slimBOXtv 9.20 ATV**: https://slimboxtv.ru/n5max-x3/ . Select the *152F* subsection.

Extract each downloaded archive to its complete Amlogic USB Burning Tool `.img`. Actual original filenames are not independently verified: **use your own paths**. The builder pins original X96 DDR/U-Boot/DTB and Magicsee boot/DTB/vendor/manifest SHA-256. Unknown revisions fail closed, rather than being silently modified.

You also need Windows 10/11, Python 3.9+, WSL2 Ubuntu with `e2fsprogs` and `android-sdk-libsparse-utils`, `AmlImagePack.exe` obtained separately, and at least **12 GiB free** for staging/verification.

Install/check WSL requirements in PowerShell:

```powershell
py -3 --version
wsl --status
wsl -u root -e bash -lc "apt update && apt install -y e2fsprogs android-sdk-libsparse-utils python3"
wsl -e bash -lc "command -v simg2img && command -v img2simg && command -v debugfs && command -v e2fsck && command -v python3"
```

## One-command build

From the repository root in Windows CMD or PowerShell (replace the **example** donor paths):

```bat
py -3 scripts\build_laki_v6.py --x96-img "C:\DonorROMs\X96-Plus5-ATV920.img" --magicsee-img "C:\DonorROMs\Magicsee-152F-ATV920.img" --packer "C:\AmlogicKitchen\bin\windows\AmlImagePack.exe" --output-root "C:\LakiBox-Backup\LAKI-V6-BUILD"
```

No donor file is downloaded or shipped here. The direct Python command requires a new output directory; the interactive launcher automatically picks a unique retry directory instead of deleting old builds. Add `--check-only` for a no-write preflight, or `--keep-work` to retain the internal unpacked directories. The standalone kit also has an interactive `RUN-V6.cmd` launcher.

## What the builder does

- Unpacks the **two original donor IMG files** and validates their firmware layout and pinned component hashes.
- Copies **Magicsee Android partitions**, including its kernel, system, vendor, product and ODM. This is essential for the Unisoc Android Bluetooth framework; an early experimental X96-system stage did not have it.
- Uses pinned **X96 DDR/U-Boot**, burn-time ini/conf and FULL manifest. **The FULL manifest contains an explicit DDR.USB `PARTITION/bootloader` record**.
- Reconstructs the **AC213 Wi-Fi interrupt** (`0x49` to `0x54`, `GPIO_IRQ_LOW` to `GPIO_IRQ_HIGH`) and Bluetooth pin property (`gpio_en` to `gpio_reset`) on X96's `sm1_ac213_2g` DTB only.
- Disables eARC and removes `/auge_sound/aml-audio-card,dai-link@6`, then rebuilds the original Magicsee-kernel boot image with the amended device tree and correct Android boot SHA-1. Exact final boot/DTB hashes are pinned to previously verified V4.1 audio partitions.
- Patches **one staged copy of Magicsee `system.PARTITION` in one ext4 pass**: adds Android 9 Bluetooth `READ_CONTACTS` XML and changes exactly three build properties: `ro.product.model=m6cw4k`, `ro.product.brand=LAKI`, `ro.build.display.id=LAKI Hybrid V6 FULL AUDIO by DarkoBG`. Preserves donor `build.prop` mode (including 0600), root ownership and its known SELinux label. Does not change `ro.product.device`, manufacturer, fingerprint or vendor partition. Model/build display and functional Bluetooth default permission were reported **PASS** on one V6 hardware test; applicability to other hardware remains unverified.
- Packs **one V6 FULL AUDIO `.img`**, re-unpacks it, checks each partition against its staging source, and verifies the manifest and X96 bootloader pair. Sources are not overwritten. Intermediate directories are deleted only after a verified successful build.

## Expected output and independent verification

```text
LAKI-V6-BUILD/
  LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img
  LAKI-V6-BUILD-REPORT.json
  SHA256SUMS.txt
```

In PowerShell:

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-V6-BUILD\LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img' -Algorithm SHA256
```

Compare the result to `output_sha256` in the generated report. The old V5.1 **whole-IMG** SHA-256 is **not** a required V6 output hash; filesystem packing can differ. The critical V6 audio payloads are SHA-256-pinned:

- `boot.PARTITION`: `A334E39C6600731A352A2DB259C1B0F6F4D24BA09EFB049BC357DF9F52E91F6B`
- `_aml_dtb.PARTITION`: `FD33629D04630DF9A437DDDD5F870FE94D6C4EE9755055B5B380DADE625FC13E`

If the build fails, it leaves an `INCOMPLETE-NOT-VALIDATED.txt` marker. **Do not flash partial outputs.**

## Limitations

- This is a **single-step build**, not a tested single-step firmware flashing method. The FULL bootloader may brick a factory-stock box; the successful V4.1 box already had the X96 bootloader installed.
- A specific V6 image passed 9/9 operator-reported functional checks on one device, including boot, Wi-Fi, Bluetooth, IPTV video and AUX audio. Cold-start endurance, other devices, and factory-stock bootloader compatibility were not established. See [hardware validation](V6_HARDWARE_VALIDATION_2026-11-01.md).
- Installed IPTV apps, DRM and user data under `/data` are not automatically included in the firmware.
- Proprietary donor ROM images, DTBs and the packer executable are not redistributed in this source repository. Users must check their licensing obligations.

Run logic tests with `py -3 -m unittest discover -s tests -v`. Tests are not hardware validation.

### Deterministic gzip patch (2026-11-01)

A previous Windows build could fail on a Wi-Fi/BT DTB compressed SHA-256 despite pinned donor partition hashes passing. `gzip.compress(mtime=0)` can write different operating-system header bytes on different Python versions. The corrected V6 uses `gzip.GzipFile(..., mtime=0, filename='', compresslevel=9)` for both Wi-Fi and audio DTBs, and checks **both uncompressed SHA-256 and the unchanged historical compressed SHA-256**. No safety pin is disabled. On a failure, leave the incomplete folder in place and select a fresh output directory.
