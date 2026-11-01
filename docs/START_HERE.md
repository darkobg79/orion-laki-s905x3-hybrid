# Start here — LAKI Hybrid firmware (step-by-step)

> **Status: November 1, 2026.** **V5.1 FULL AUDIO RC1** was independently SHA-256-verified and subsequently **physically flashed, booted and functionally tested on one previously X96-modified LAKI M6CW4K**. Wi-Fi/Internet, Bluetooth pairing/audio, IPTV video, AUX and reboot passed. **Not tested on an untouched factory Orion bootloader or other revisions.** [Evidence](V5_1_HARDWARE_VALIDATION_2026-11-01.md).
>
> This is an **offline build guide**, **not a flashing tutorial**. No prebuilt proprietary firmware IMG or DTB files are distributed here.

**Choose your starting point:**

- **A. Just want to download and explore the project?** Follow steps 1–3.
- **B. Already have the previously built/verified V5 FULL and V4.1 images plus the local reference DTB?** Follow steps 1–8.
- **C. Only have a stock LAKI box or two downloaded donor ROMs?** Read [What you cannot build from scratch yet](#what-you-cannot-build-from-scratch-yet). The current scripts **cannot** make V5.1 directly from the two donor ROM downloads.

## 1. Check your hardware — no flashing

The only documented successful hardware test is **Orion LAKI M6CW4K**, **Amlogic S905X3 / SM1**, **AC213 board**, **2 GB RAM / 16 GB storage**, **Unisoc UWE5621** Wi-Fi/Bluetooth. If ADB is *already* available, read-only checks:

```bat
adb shell "cat /proc/device-tree/amlogic-dt-id"
adb shell "cat /proc/meminfo | head -n 3"
adb shell "uname -a"
```

See [HARDWARE.md](HARDWARE.md). Similar branding does not guarantee identical DDR, board wiring or bootloader compatibility.

## 2. Download OUR project source from GitHub

1. Open the [LAKI Hybrid repository](https://github.com/darkobg79/orion-laki-s905x3-hybrid).
2. To download a specific release snapshot, click **Releases** → **v5.1.0-rc1** → **Source code (zip)**. **This is code and documentation, NOT a ready-to-flash IMG.** Documentation added after the tag may only appear on the latest `main` branch.
3. Alternatively, for the **latest source**, click the green **Code** button → **Download ZIP** on the repository homepage. Latest `main` may differ from the release tag.
4. Extract the ZIP, e.g. to `C:\GitHub\orion-laki-s905x3-hybrid`. Check for `scripts\build_laki_v51_full_audio.py` and `docs\V5_1_FULL_AUDIO.md`.

Git cloning is optional; the ZIP is enough for reading or running the scripts.

## 3. Get donor firmware from the original authors' websites

These are **third-party firmware sources, not our hybrid output**:

| Source page | Where to click | Exact donor edition | Intended role |
| --- | --- | --- | --- |
| [slimBOXtv — X96 Max Plus](https://slimboxtv.ru/x96max-plus/) | Find **“Для ревизии Plus 5”** → **“Скачать ATV или AOSP”** | **Plus 5**, slimBOXtv **9.20 ATV** | Previously working X96 DDR/U-Boot components |
| [slimBOXtv — Magicsee N5 Max X3](https://slimboxtv.ru/n5max-x3/) | Find **“Для ревизии 152F WiFi чип Unisoc uwe5621ds”** → **“Скачать ATV или AOSP”** | **152F / UWE5621DS**, slimBOXtv **9.20 ATV** | Kernel / Android / Unisoc stack |

Choose **ATV**, not AOSP, and do not substitute another board revision. Do not guess the downloaded archive or IMG filename. The downloads may require a separate host/login. Follow the original authors' terms of use and redistribution.

**Downloading these two images alone is not enough** for the current published V5.1 builder (see below).

## 4. Install tools on Windows

For the V5.1 *composer* you need:

- Windows 10/11;
- **Python 3.9 or later** ([python.org/downloads](https://www.python.org/downloads/)), with `py -3` available;
- Your own legally obtained **AmlImagePack.exe**, example location `C:\AmlogicKitchen\bin\windows\AmlImagePack.exe`;
- **At least 9 GiB free** for output and unpack/verify stages;
- The **pre-existing local IMG/DTB inputs** listed in step 5.

Check from PowerShell:

```powershell
py -3 --version
Test-Path 'C:\AmlogicKitchen\bin\windows\AmlImagePack.exe'
Get-PSDrive C
```

The older **V4 → V5 NOBOOTLOADER** system-partition process also requires WSL2 Ubuntu and ext4/sparse utilities; see [BUILD.md](BUILD.md). V5.1 itself is a Windows-only composer but requires the earlier V5 FULL image.

## 5. Supply the required local inputs

These are **previously built by the operator**, not published binaries or downloads from this repository:

```text
C:\LakiBox-Backup\
    LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img
    LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img
```

You also need your **own** `laki-v4-running.dtb` from the earlier V4 audio-test kit or backup. The binary DTB is **not shipped here**. Example local path (replace as necessary):

```text
C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb
```

Hash verification:

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img' -Algorithm SHA256
Get-FileHash 'C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb' -Algorithm SHA256
```

Expected SHA-256:

```text
V5 FULL: AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9
V4 DTB:  5D3902B74AD206078503051C858BE97963B7307F21D102C20A078C75E5A900FC
```

There is no published reference hash for the complete V4.1 image. The builder instead **independently re-computes and compares both audio payloads** against the expected eARC-off patch. **Never supply an arbitrary downloaded S905X3 image in place of these specific inputs.**

## 6. Run tests and preflight (no image output)

Open PowerShell in the extracted project folder. You can open the folder in File Explorer and type `powershell` into its address bar:

```powershell
py -3 -m unittest discover -s tests -v
```

Check the required files, hashes, tool path and free space (change the local DTB path as needed):

```powershell
py -3 scripts\build_laki_v51_full_audio.py --check-only --reference-dtb 'C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb' --output-root 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD'
```

`--check-only` performs preliminary checks **without unpacking all partition data**, and writes no output. A `STOP` error means you should correct the inputs; do not bypass integrity checks.

## 7. Build V5.1 FULL AUDIO offline

Run the same command without `--check-only`:

```powershell
py -3 scripts\build_laki_v51_full_audio.py --reference-dtb 'C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb' --output-root 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD'
```

The `--output-root` directory **must not exist yet**. The builder refuses to overwrite existing work. It will unpack the two input IMG files, re-compute/verify the V4.1 eARC patch, replace **only** `boot.PARTITION` and `_aml_dtb.PARTITION` in a copy of V5 FULL, pack, unpack and verify the result, and generate a JSON report.

Expected outputs:

```text
C:\LakiBox-Backup\LAKI-V5.1-REBUILD\
    LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img
    LAKI-V5.1-FULL-AUDIO-BUILD-REPORT.json
```

## 8. Verify output — then STOP before flashing

```powershell
Get-FileHash 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD\LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img' -Algorithm SHA256
Get-Content 'C:\LakiBox-Backup\LAKI-V5.1-REBUILD\LAKI-V5.1-FULL-AUDIO-BUILD-REPORT.json'
```

Known hash of the previously built image:

```text
B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378
```

A different top-level hash in a future build **does not automatically mean success or failure**: inspect provenance and the per-partition JSON report, as packaging may differ. Successful pack/unpack does **not** prove hardware functionality.

> [!CAUTION]
> **DO NOT AUTO-FLASH THE RESULT.** FULL contains an explicit X96 `PARTITION/bootloader` manifest record. On 2026-11-01 V5.1 was successfully flashed on **one already X96-modified device**, with erase-data and erase-bootloader options selected, but a failed DDR/U-Boot write can still brick another unit. **Untouched stock Orion bootloader and other revisions remain untested; no universal safe checkbox combination exists.** Read [FLASHING.md](FLASHING.md) and [hardware validation](V5_1_HARDWARE_VALIDATION_2026-11-01.md).

## What you cannot build from scratch yet

**The public repository is not a one-click two-donor-ROM-to-V5.1 solution yet.**

- [`finalize_laki_v5.py`](../scripts/finalize_laki_v5.py) requires a **previously assembled V4 staging folder** and a matching V4 image.
- [`build_laki_v5_full.py`](../scripts/build_laki_v5_full.py) requires an existing V5 NOBOOTLOADER image, staging files and JSON build report.
- [`build_laki_v51_full_audio.py`](../scripts/build_laki_v51_full_audio.py) requires exact V5 FULL and V4.1 files plus a **local reference DTB**.
- Fully automated **V4 hybrid assembly from the two donor ROMs** and the full V4.1 audio patch/build from those raw inputs have **not** been completed and independently validated as a public end-to-end process.

If you lack the required inputs, **stop at step 3**. Do not fabricate matching filenames or disable SHA-256 checks. A proper source-to-V4/V4.1 builder with repeatable partition validation is a future project task.

## Help and further documentation

- [Historical V4 → V5 build chain](BUILD.md)
- [V4.1 audio and HDMI diagnostics](V4_1_AUDIO.md)
- [V5.1 FULL AUDIO technical record](V5_1_FULL_AUDIO.md)
- [Flashing and recovery risks](FLASHING.md)
- [Hardware compatibility](HARDWARE.md)
- [Open an issue](https://github.com/darkobg79/orion-laki-s905x3-hybrid/issues/new/choose)

Redact passwords, tokens, serial numbers, MAC addresses, account identifiers and IP addresses from shared logs.
