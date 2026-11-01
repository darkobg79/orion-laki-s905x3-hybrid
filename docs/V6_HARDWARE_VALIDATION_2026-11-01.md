# LAKI Hybrid V6 FULL AUDIO by DarkoBG — physical validation

**Date:** 2026-11-01  
**Evidence:** operator-reported hardware flash and nine functional checks on a real Orion LAKI box. Detailed raw USB Burning Tool logs, post-flash partition readback, and independent bootloader analysis have not been supplied.  
**Result:** **9/9 PASS on one device**. This is not a universal compatibility certification.

## Image and provenance

| Field | Verified / reported value |
| --- | --- |
| Version | `6.0.0` |
| Image | `LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img` |
| Full IMG SHA-256 | `ABB9B548159192D7379BEFBB2D34B45FF85DACF2A6EB4209631635AD8F079F9E` |
| Image size | 1,337,430,864 bytes |
| Build report | `LAKI-V6-BUILD-REPORT.json` |
| Build result | Amlogic pack/unpack and per-partition SHA-256 verification passed |
| Independent check | Windows `certutil -hashfile ... SHA256` matched the report's IMG hash |
| Device | Orion LAKI M6CW4K; Amlogic S905X3 / SM1; AC213; 2 GB RAM / 16 GB; Unisoc UWE5621 |

Source IMG fingerprints, as recorded in the local build report:

- X96 Max Plus 5 ATV 9.20: `197186CE54C78E6C4D19B4DCAC7CF30BF9E6B596D1E9EF3B9F310723E30085B1`.
- Magicsee N5 Max X3 152F ATV 9.20: `FBA4347CBCA7BF22E700C1A455BEDBC23C02D4E8CDDEBA0060AC31FC769F5788`.

The image was built **directly from the two donor IMG files**, without V4/V4.1/V5/V5.1 intermediary input images. The builder combined the pinned X96 DDR/U-Boot, the Magicsee Android/kernel/vendor payloads, reconstructed known AC213 Wi-Fi/BT and V4.1 eARC adjustments, and patched Android 9 `system.PARTITION` in one pass. Firmware fingerprint and internal device identifiers were left unchanged; Android model `m6cw4k`, brand `LAKI`, and display ID `LAKI Hybrid V6 FULL AUDIO by DarkoBG` were added.

## Operator-reported hardware results

| Test | Result |
| --- | --- |
| Android boots normally after flashing | ✅ PASS |
| Displayed model `m6cw4k` and V6 firmware name are correct | ✅ PASS |
| Wi-Fi connection and Internet access | ✅ PASS |
| Bluetooth discovers and pairs with devices | ✅ PASS |
| Bluetooth audio works | ✅ PASS |
| IPTV video playback without freezing | ✅ PASS |
| Analog AUX audio works | ✅ PASS |
| Normal restart completes | ✅ PASS |
| Bluetooth permission works without a manual ADB grant | ✅ PASS |

**Bluetooth caveat:** the functional check confirms that the operator did not need to issue a manual ADB grant; it does not substitute for an independently captured Android permission state or a detailed first-boot log.

## Hardware scope and risks

This success concerns **one Orion LAKI device**. The previous V5.1 tests were conducted on a box already modified with an X96 bootloader. A separate, untouched, factory-stock Orion bootloader test was **not** performed for V6. V6 FULL contains an explicit X96 `PARTITION/bootloader` record. Do not extrapolate the results to other board revisions, DDR layouts, or stock bootloaders; never assume a universal safe combination of `Erase flash`, `Erase bootloader`, or `Overwrite key` options.

Not independently validated: exact post-flash bootloader bytes, stock-bootloader compatibility, recovery from failed flashing, HDMI/CEC, DRM/certification, OTA, prolonged stability, and other boxes. No raw firmware or proprietary donor binary is redistributed in this source repository.

Related: [V6 one-step build instructions](V6_ONE_STEP.md), [Srpsko uputstvo](V6_ONE_STEP.sr.md), [V5.1 hardware record](V5_1_HARDWARE_VALIDATION_2026-11-01.md), [flashing risks](FLASHING.md).
