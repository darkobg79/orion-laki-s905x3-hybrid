# Tested hardware and compatibility checks

## Device on which V4 worked

- Orion LAKI TV Box; Amlogic S905X3 / SM1; AC213 board.
- 2 GB RAM / 16 GB eMMC (observed).
- Original device-tree ID: `sm1_ac213_g10xc2g`.
- Hybrid device-tree ID: `sm1_ac213_2g`.
- Unisoc UWE5621 combo SDIO Wi-Fi and Bluetooth radio.
- On V4: Linux 4.9.113, tested on Android 9 / ATV user space.
- Tested over Ethernet and 2.4/5 GHz Wi-Fi network discovery/association (exact band of the connected AP not established).

## Read-only identification via ADB

When ADB is already enabled on a device:

```bat
adb devices -l
adb shell "cat /proc/device-tree/amlogic-dt-id"
adb shell "cat /proc/meminfo | head -n 3"
adb shell "cat /proc/partitions"
adb shell "uname -a"
adb shell "cat /proc/modules | grep -E 'uwe5621|sprdwl|sprdbt'"
```

A stock image may use different kernel module names and `/proc/device-tree` paths. Inspect the actual board printing/markings and memory chips where safe. Match **DDR memory initialization requirements**, not merely the Android device model.

## Why the AC213 DT matters

The donor X96 device tree was not identical to the LAKI/AC213 wiring. The hybrid DT was adapted for the 2 GB AC213 board and wireless control lines, including a Wi-Fi interrupt pin/polarity and Bluetooth control function difference. This adaptation was necessary for the tested UWE5621 configuration; its pin assignments should **not** be blindly applied to another hardware revision.

## Compatibility checklist before any full flash

- Same Amlogic SoC and SM1 boot chain.
- Same board revision and device-tree electrical configuration.
- Same RAM type, density, wiring and DDR training assumptions.
- Compatible eMMC geometry and boot partitions.
- Same Unisoc UWE5621 combo chip and antenna/radio wiring.
- Known stock firmware backup and feasible recovery path.

**Passing an ADB check cannot guarantee bootloader compatibility.** Bootloader replacement failures may occur before Android, ADB or USB burning can operate.
