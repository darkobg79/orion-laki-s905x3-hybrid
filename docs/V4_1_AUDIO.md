# LAKI Hybrid V4.1 — verified audio and HDMI behavior

**Test date:** 2026-11-01. **Test hardware:** one Orion LAKI M6CW4K, Amlogic S905X3 (SM1), AC213, 2 GB RAM / 16 GB storage, Android TV 9.20 / Android 9.

> **Scope:** V4.1 was flashed and tested on **one** device. This document is not a universal flashing guide. No V4.1 IMG or proprietary firmware is included. The exact packed V4.1 IMG SHA-256 is **not documented here**; verify the local file independently before distributing or flashing it.

## Why V4.1 was necessary

The earlier V4 hybrid enabled Unisoc UWE5621 Wi-Fi and Bluetooth, but showed `No soundcards found` in ALSA and IPTV video could freeze at the first frame after audio initialization failed. Accordingly, **V4 must not be described as fully working for IPTV/AUX sound**.

The locally packed **`LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img`** addressed audio registration by disabling the incompatible eARC device-tree node and removing `aml-audio-card,dai-link@6`. Both `boot.PARTITION` and `_aml_dtb.PARTITION` were patched; the remaining DAI links and other partition payloads were preserved/checked in the local pack-and-unpack process. These V4.1 operations are **not implemented by the existing V5 build scripts**. The patch is specific to this test board and kernel; do not copy it onto unrelated hardware.

After flashing, the card `AML-AUGESOUND` registered and IPTV video played normally. Analog AUX, Bluetooth audio, Wi-Fi and Android TV were observed working.

## Verified ALSA and codec details

Read-only ADB commands:

```bat
adb shell "cat /proc/asound/cards; cat /proc/asound/pcm"
adb shell "cat /proc/device-tree/auge_sound/compatible"
adb shell "cat /proc/device-tree/amlogic-dt-id"
adb shell "cat /proc/asound/card0/pcm1p/sub0/hw_params"
adb shell "cat /sys/kernel/debug/gpio | grep avout_mute"
```

Observed: card 0 `AML-AUGESOUND`; TDM-A (PCM 0), **TDM-B (PCM 1)**, TDM-C (PCM 2), PDM (PCM 3), SPDIF (PCM 4), SPDIF-B (PCM 5). Sound card compatible: `amlogic, g12a-sound-card`. Hybrid DT ID: `sm1_ac213_2g`. Internal T9015 properties: `is_auge_used=1`, `tocodec_inout=1`, `tdmout_index=1`, `ch0_sel=0`, `ch1_sel=1`.

During IPTV playback the HAL used TDM-B, `S16_LE`, stereo, **48 kHz**, period size `512`, buffer size `3072`. The hardware PCM frame pointer advanced at the expected 48 kframes/s. The Android primary AudioFlinger output was `AUDIO_DEVICE_OUT_SPEAKER` (`0x2`), stereo 16-bit PCM, 48 kHz; the AudioFlinger signal power history showed non-silent audio data.

## AUX sound was initially effectively inaudible because MEDIA volume was low

Android `STREAM_MUSIC` was initially **17/65**. Sound became audible over the same physical AUX/AV cable when it was increased to **55/65**, and also worked at **50/65**:

```bat
adb shell media volume --stream 3 --get
adb shell media volume --stream 3 --set 50
adb shell media volume --stream 3 --get
```

**Turn down the physical speaker/amplifier before raising Android volume.** `50/65` is a tested example, not a recommended universal default. Avoid confusing Android's media volume with the separate ALSA `DAC Digital Playback Volume` control (observed `251/255`).

The `tinymix -D 0` values did not differ between audio HAL running/stopped or during IPTV playback. The `/vendor/etc/mixer_paths.xml` on the test ROM was an intentional dummy containing empty `speaker` and `headphone` paths; 206 bytes is not itself evidence of a broken configuration. An ALSA mixer comparison does not capture all possible HAL operations.

## Direct analog output test, with exclusive ALSA access

With Android running, the audio HAL continuously owned TDM-B (PCM owner thread from `/vendor/bin/hw/android.hardware.audio@2.0-service`), even on the home screen. Running `tinyplay` concurrently did not provide an isolated test.

On the rooted test unit, **temporarily stopping both** `audioserver` and `vendor.audio-hal-2-0` freed the PCM endpoint (`closed`). Direct playback of a known-valid 3-second, stereo, 48 kHz, 16-bit PCM WAV through **card 0/device 1** was audible on the AUX jack:

```bat
adb shell "su -c 'setprop ctl.stop audioserver; setprop ctl.stop vendor.audio-hal-2-0; sleep 2; getprop init.svc.audioserver; getprop init.svc.vendor.audio-hal-2-0; cat /proc/asound/card0/pcm1p/sub0/status'"
adb shell "su -c 'tinyplay /data/local/tmp/aux-test.wav -D 0 -d 1'"
adb shell "su -c 'setprop ctl.start vendor.audio-hal-2-0; setprop ctl.start audioserver'"
adb shell "getprop init.svc.audioserver; getprop init.svc.vendor.audio-hal-2-0"
```

The WAV was uploaded separately for local diagnosis and **is not shipped with this repo**. Run `tinyplay` only after verifying both services are `stopped` and PCM is `closed`. This interrupts Android audio and may disturb running apps; restore services or reboot after testing. Do not use this routine on a non-rooted or critical device.

## ONTEN HDMI switch observations

| ONTEN selected input | LAKI HDMI HPD | LAKI video mode |
| --- | --- | --- |
| HDMI 1: PC | `0` | `576cvbs` |
| HDMI 2: LAKI | `1` | `1080p60hz` |

With different media volume indices (`39/65` with PC selected and `36/65` with LAKI selected), analog sound initially appeared louder on the PC selection. **When media volume was manually set to `50/65` in both selections, perceived AUX loudness became equal.** Thus the switch position itself was not shown to change analog output gain at fixed Android volume; the cause of earlier volume drift was not established. HDMI-CEC or remote-control interaction is a hypothesis, not a proven finding.

The audio HAL log showed a `SPEAKER` → `HDMI` routing attempt and `outport = HDMI unsupport`; this did not prevent audible AUX playback after correcting the volume. Do not modify audio policy based on that message alone.

```bat
adb shell "cat /sys/class/amhdmitx/amhdmitx0/hpd_state; cat /sys/class/display/mode; media volume --stream 3 --get"
```

## Do not invert GPIO `avout_mute`

The kernel exposed `gpio-498 (...|avout_mute) out hi` before **and during audible AUX playback**. The stock and hybrid DTBs both map `avout_mute` to `GPIOAO_2`; an `out hi` debug label is **not proof** of a muted analog path. Do not blindly invert its polarity or force a value using `devmem`.

## Verification boundaries

**Physically observed working on this first unit:** Android boot, Wi-Fi, Bluetooth pairing/speaker audio, moving IPTV picture, IPTV audio over analog AV/AUX, direct ALSA analog tone. This is not a long-term stability certification.

**Not confirmed:** V4.1 on an untouched stock-bootloader box; V4.1 packed IMG SHA-256 in the repository; media volume persistence specifically across a verified cold reboot; cause of the earlier volume changes; clean-install behavior of V5. **V5 NOBOOTLOADER and V5 FULL remain offline-verified only, not physically flashed.**

See [BUILD.md](BUILD.md) for the *separate* V5 workflow and [FLASHING.md](FLASHING.md) for bootloader and recovery risks.
