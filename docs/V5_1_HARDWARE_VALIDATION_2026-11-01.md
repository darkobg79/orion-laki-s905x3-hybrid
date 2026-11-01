# LAKI Hybrid V5.1 FULL AUDIO — physical hardware validation

**Date:** 2026-11-01  
**Evidence:** first-person operator report from a physical flash and functional checks. Detailed USB Burning Tool logs, partition-readback and video recordings were not supplied.  
**Status:** **hardware-flashed and functionally tested on one previously modified LAKI M6CW4K**; not certified for other revisions or an untouched stock Orion bootloader.

## Exact image reported as tested

- Local build folder: `C:\LakiBox-Backup\LAKI-V5.1-FULL-AUDIO-BUILD\`
- IMG: `LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img` (historical output name)
- SHA-256 (previously independently re-read from the completed local image):
  `B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378`
- Contents: V5 FULL Android system/vendor and X96 FULL manifest, with V4.1 audio-corrected `boot.PARTITION` and `_aml_dtb.PARTITION`.
- Previous evidence: image pack/unpack and partition-level SHA-256 validation.

## Flash conditions — operator report

- Hardware: Orion LAKI M6CW4K, Amlogic S905X3 / SM1, AC213, 2 GB RAM / 16 GB storage, Unisoc UWE5621.
- Device history: **this device had already received an X96 bootloader in an earlier firmware experiment**. It was **not** an untouched factory-bootloader device.
- USB flash: operator used data-erase **and** bootloader-erase options, and reports the V5.1 FULL AUDIO image flashed and booted successfully.
- Crucial limitation: selecting an erase-bootloader option and then booting successfully does **not**, by itself, constitute an independent readback proof of which bootloader bytes were rewritten. No raw readback is documented.

## Confirmed after the V5.1 flash

| Check | Operator report |
| --- | --- |
| Android startup after flashing | **PASS** |
| Wi-Fi association and Internet access | **PASS** |
| Bluetooth device discovery and pairing | **PASS** |
| Bluetooth audio | **PASS** |
| IPTV video playback without freezing | **PASS** |
| Analog AUX audio output | **PASS** |
| Normal reboot back into Android | **PASS** |

**Not separately established:** automatic `READ_CONTACTS` default-permission application on first boot (there is no documented before/after permission dump or confirmation that no manual grant was used); HDMI audio, HDMI-CEC, DRM/streaming certification, OTA, deep sleep, prolonged stability, recovery from a failed flash, alternative board revisions or untouched stock Orion bootloader compatibility.

## Scope of this milestone

This is a significant **one-device hardware success for V5.1 FULL AUDIO**. Do not transfer its status to the **earlier distinct V5 NOBOOTLOADER** or **V5 FULL (without V4.1 audio)** image, which remain offline-only. It also does not prove the proposed **V6 one-step builder** or its eventual output has passed full donor-to-IMG and physical tests.

The project does not distribute proprietary prebuilt IMG/DTB blobs. Confirm redistribution rights before releasing any donor-derived firmware.

Related: [V5.1 build record](V5_1_FULL_AUDIO.md), [flashing risks](FLASHING.md), [V4.1 audio diagnostics](V4_1_AUDIO.md).
