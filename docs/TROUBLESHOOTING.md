# Troubleshooting notes from the tested build

**2026-11-01 update:** V4.1 restores ALSA and IPTV picture; analog sound worked after fixing low Android MEDIA volume. See [V4.1 audio diagnostics](V4_1_AUDIO.md) before touching GPIO, DTB or HAL.

## USB Burning Tool halts near 7%

Observed on unmodified Magicsee-derived images:

```text
[0x32030201] Uboot/Get result/DiskInitial error
```

Repeated failure at the same early percentage suggested a DDR/U-Boot or device initialization incompatibility. The working hybrid used DDR/USB U-Boot components from a previously successful X96 image instead of the failing Magicsee pair. **This does not prove a universal solution for all boards**; stop if your hardware differs.

## Wi-Fi missing in Android after a successful boot

A ROM can boot without a compatible Unisoc kernel+vendor stack. Merely copying `.ko` files from a different kernel led to CRC mismatch / missing symbol errors during early testing.

Read-only checks on the tested hybrid:

```bat
adb shell "cat /proc/modules | grep -E 'uwe5621|sprdwl|sprdbt'"
adb shell "ip addr show wlan0"
adb shell "dmesg | grep -i -E 'sdio|uwe5621|sprdwl' | tail -n 70"
```

The V4 device loaded `uwe5621_bsp_sdio`, `sprdwl_ng`, and `sprdbt_tty` and obtained a Wi-Fi IP address.

## Bluetooth settings show a search screen but nothing works

Opening the Android Bluetooth device-search activity **does not demonstrate** that the adapter has initialized. Inspect the crash and state logs first:

```bat
adb shell "dumpsys bluetooth_manager | head -n 25"
adb shell "logcat -b crash -d -v threadtime | tail -n 120"
adb shell "getprop | grep -i bluetooth"
```

In V4 the Bluetooth adapter crashed hundreds of times because the `BluetoothPbapService` lacked `READ_CONTACTS` permission. On the rooted test device, the following command fixed this **specific** crash:

```bat
adb shell pm grant com.android.bluetooth android.permission.READ_CONTACTS
```

Verify:

```bat
adb shell "dumpsys package com.android.bluetooth | grep -i -A 3 READ_CONTACTS"
adb shell "dumpsys bluetooth_manager | head -n 7"
```

Then test discovery, pairing, and audio **on actual hardware**. The permission grant was found by reading `logcat`, not by trial-and-error permission changes.

## `btwrite` permission error

The vendor HAL also logged:

```text
bt_upio : open(/proc/bluetooth/sleep/btwrite) for write failed: Permission denied (13)
```

It was **not necessary** to change permissions on `/proc/bluetooth/sleep/btwrite` for V4 to discover, pair and output audio after the PBAP permission fix. Do not globally `chmod 777`, relax SELinux policy or modify live kernel interfaces based solely on this line.

SELinux `avc: denied ... permissive=1` audit records appeared in the experiment. In permissive mode, these audit messages alone do **not** prove enforcement blocked the operation.

## Still seeing `Bluetooth crashed 664 times`

The number reported by `dumpsys bluetooth_manager` was a cumulative history counter. After the `READ_CONTACTS` grant, the adapter remained `ON` for over ten minutes and the latest fatal crash entries were timestamped **before** the fix. Use timestamps and a fresh controlled test to distinguish old log history from a new crash.

## V5 offline pass but Bluetooth remains broken on a clean flash

V5 only adds a system default-permissions exception. It does **not** replace the ROM's Bluetooth APK, HAL, kernel driver, or framework. The Android 9 first-boot permission application is still untested on physical V5, so verify the grant in `dumpsys package` and inspect the new crash log before modifying anything.
