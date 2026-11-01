# Flashing and recovery risks — read before using an IMG

> [!CAUTION]
> **No flashing tutorial here can make replacing an early Amlogic DDR/U-Boot bootloader safe for an unverified board.** A failed bootloader write can make a device inaccessible to ADB, recovery and normal USB Burning mode. Recovering such a device may require specialized hardware techniques.

## Evidence and limitations

- On 2026-11-01, **V4.1** (locally repacked eARC/DTB audio correction) was physically flashed and tested on the same previously modified box. IPTV video and AUX audio worked. This does **not** validate clean flashing from a stock bootloader, and **does not** validate any V5 image. See [V4.1 evidence](V4_1_AUDIO.md).

- The **first physical box** was originally flashed with a compatible X96 Max Plus 5 ROM and its bootloader replacement option was enabled.
- Later the **V4 hybrid** (without an explicit `PARTITION/bootloader` entry) flashed successfully, booted, and passed Wi-Fi and Bluetooth audio tests.
- The original Magicsee ROM failed early with `DiskInitial` at ~7%.
- V5 NOBOOTLOADER and V5 FULL were **never physically flashed** during the documented work.
- The **V5.1 FULL AUDIO** image was built on 2026-11-01 and verified offline (including a separate image SHA-256 read). It **has not been physically flashed**. Its FULL manifest retains the explicit X96 `PARTITION/bootloader` entry. See [V5.1 build notes](V5_1_FULL_AUDIO.md).
- The second, stock box was **not yet hardware-verified or tested**.

Thus V4 working on the first box is **not evidence that the second stock box will accept V5 FULL in a single flash**.

## NOBOOTLOADER is not a universal safety guarantee

The `NOBOOTLOADER` image omits an explicit `PARTITION/bootloader` manifest entry, but still carries USB DDR and burn-time U-Boot components. Tool-specific flags and USB bootstrap behavior matter. **Do not assume it is technically impossible for a tool to change the bootloader** when an image is called NOBOOTLOADER.

The `FULL` image adds back an explicit X96 bootloader partition record. That record alone is not proof a given USB Burning Tool session actually overwrites the eMMC bootloader.

## Before considering any flash

1. Identify exact PCB revision, SoC, DDR configuration, eMMC, and radio chip on the target.
2. Keep a **verified full stock backup**, including bootloader-related partitions and Android partitions. Raw partition backups by themselves do **not** guarantee recovery from a dead early bootloader.
3. Confirm that the recovery path actually works for that target unit, preferably without modifying its bootloader.
4. Check SHA-256 of the intended file against your own known reference and the reported build provenance.
5. Preserve working V4 and V5 originals; never test on the only functional device unless the recovery risk is acceptable.
6. Determine whether a clean flash would remove an operator IPTV app or other user data. A separately installed APK in `/data` may not be inside the system image.

## USB Burning Tool options

The options **Erase flash**, **Erase bootloader**, **Overwrite key** and **Reset after success** are not interchangeable. Do not automatically enable any erase or key-overwrite checkbox based on someone else's screenshot. For the original conservative V4 experiment, erase/bootloader overwrite were disabled. The earlier X96 firmware had been flashed under a different set of options.

**This repository deliberately does not prescribe settings for flashing V5 FULL onto an unverified stock box.** Validate the hardware and document a recovery strategy first.

## Validating a completed operation

A `100%` progress bar alone is insufficient: verify the explicit success status in the flasher and then confirm on-device boot, Wi-Fi association, Bluetooth state, discovery, pairing and audio.

On a device with **already enabled ADB**:

```bat
adb shell "cat /proc/device-tree/amlogic-dt-id"
adb shell "cat /proc/modules | grep -E 'uwe5621|sprdwl|sprdbt'"
adb shell "dumpsys package com.android.bluetooth | grep -i -A 3 READ_CONTACTS"
adb shell "dumpsys bluetooth_manager | head -n 7"
```

Do not claim V5 or a second board is verified until those tests are done on actual hardware.
