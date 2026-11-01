# LAKI Hybrid V6.0.0 FULL AUDIO by DarkoBG

**First end-to-end One-Step build and physical validation on one previously modified Orion LAKI device.**

## Validated result — 2026-11-01

- **9/9 operator-reported hardware checks PASS:** Android boot; correct model/build display; Wi-Fi and Internet; Bluetooth discovery/pairing; Bluetooth sound; IPTV video without freezing; analog AUX sound; reboot; and Bluetooth permission functioning without manual ADB grant.
- Built from **two original donor IMG files only** (X96 Max Plus 5 ATV 9.20 + Magicsee N5 Max X3 152F ATV 9.20), with **no V4/V4.1/V5/V5.1 intermediate images**.
- Image unpack/repack and per-partition SHA-256 comparison passed; an independent Windows `certutil` check matched the build report.
- Brand/display: `ro.product.model=m6cw4k`, `ro.product.brand=LAKI`, `ro.build.display.id=LAKI Hybrid V6 FULL AUDIO by DarkoBG`.
- AC213 Wi-Fi/BT and V4.1 eARC audio patches retained; the original Magicsee kernel and selected Android components retained. The Bluetooth default-permission XML and cosmetic properties are applied to the `system` partition in a single pass.

**Verified local IMG (NOT distributed here):** `LAKI-Hybrid-V6-FULL-AUDIO-by-DarkoBG.img`  
**SHA-256:** `ABB9B548159192D7379BEFBB2D34B45FF85DACF2A6EB4209631635AD8F079F9E`  
**Size:** 1,337,430,864 bytes.

## What's included in this GitHub release

**Source code, Windows launcher, tests and build documentation only.** No proprietary, ready-to-flash IMG, donor bootloader, DTB, kernel, vendor firmware, IPTV application or DRM/key file is distributed. Obtain original donor ROMs separately, subject to their respective terms.

Use [V6 one-step build instructions](docs/V6_ONE_STEP.md), [srpsko uputstvo](docs/V6_ONE_STEP.sr.md), and [hardware validation record](docs/V6_HARDWARE_VALIDATION_2026-11-01.md).

## Important safety limitation

**One modified box passing 9/9 is not validation for a factory-stock Orion bootloader, other hardware revisions, OTA, DRM, long-term reliability or safe recovery.** V6 FULL embeds an X96 bootloader record. Do **not** blindly use `Erase bootloader`, `Erase flash` or `Overwrite key`; review the [flashing risks](docs/FLASHING.md) and preserve the tested V5.1 fallback. No universal flashing recipe is claimed.

**V5.1 FULL AUDIO remains documented separately** as the previous hardware-tested fallback; its exact IMG and SHA-256 are unchanged.
