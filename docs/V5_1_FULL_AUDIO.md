# LAKI Hybrid V5.1 FULL AUDIO — offline build and verification

**Status (2026-11-01): PACKED AND OFFLINE VERIFIED; NOT FLASH-TESTED.**

The V5.1 FULL AUDIO image combines the previously offline-verified **V5 FULL X96 BOOTLOADER** image with the two tested audio partitions from the physically booted **V4.1 AUDIO EARC OFF** image. It preserves the V5 Android `system` partition (including the intended Bluetooth `READ_CONTACTS` default-permission change), `vendor` and the X96 FULL bootloader manifest.

| Locally built artifact | SHA-256 | Validation |
| --- | --- | --- |
| `LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img` | `B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378` | Pack, unpack, per-partition comparison, and separate `Get-FileHash` reading passed on 2026-11-01; **not booted** |

The file was built locally in `C:\LakiBox-Backup\LAKI-V5.1-FULL-AUDIO-BUILD\`, **not** uploaded to this repo. The result hash is specific to this build, not a guarantee of compatibility with other hardware. The corresponding JSON report is `LAKI-V5.1-FULL-AUDIO-BUILD-REPORT.json` in the local build directory. The earlier build was performed using the original offline kit before the source-publication change described below; these published scripts have been syntax/unit tested, but not rerun end-to-end on the Windows machine against its original large IMG inputs.

## Sources and exact changes

Required local files (not distributed here):

- `C:\LakiBox-Backup\LAKI-Hybrid-V5-FULL-X96-BOOTLOADER-UNTESTED.img`, SHA-256 `AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9`.
- `C:\LakiBox-Backup\LAKI-Hybrid-V4.1-AUDIO-EARC-TEST.img`, the **same physical-device-tested image** from the V4.1 work. The top-level hash is read and recorded at build time; no guessed reference hash is supplied.
- The previously captured **local** `laki-v4-running.dtb`, SHA-256 `5D3902B74AD206078503051C858BE97963B7307F21D102C20A078C75E5A900FC`. Obtain it from the operator's previous V4 audio-test kit or the operator's own backup. **Do not commit the binary DTB to GitHub.**
- `C:\AmlogicKitchen\bin\windows\AmlImagePack.exe` (locally installed), Windows, Python 3.9+, approximately 9 GiB free space.

The new build only replaces `boot.PARTITION` and `_aml_dtb.PARTITION` in V5 FULL with the V4.1 counterparts. The tool independently recomputes the narrowly scoped eARC device-tree patch (disable `/soc/bus@ff663000/earc@0`, remove `/auge_sound/aml-audio-card,dai-link@6`) and refuses to build if the V4.1 partitions do not match it exactly. It verifies other V4.1 payloads match the V5 source where applicable, preserves `system`/`vendor` and all other V5 FULL payloads, enforces an explicit single `DDR.USB` `PARTITION/bootloader` record, and checks SHA-256 after repack and subsequent unpack.

## Building from the published scripts (Windows PowerShell or CMD)

From the repository root, with **your own local DTB path** (change the example path to the actual location where your prior kit was extracted):

```powershell
py -3 scripts\build_laki_v51_full_audio.py --check-only --reference-dtb "C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb" --output-root "C:\LakiBox-Backup\LAKI-V5.1-REBUILD"
```

If the preflight succeeds and you have sufficient disk space:

```powershell
py -3 scripts\build_laki_v51_full_audio.py --reference-dtb "C:\LakiBox-Backup\V5.1-AUDIO-KIT\laki-v4-running.dtb" --output-root "C:\LakiBox-Backup\LAKI-V5.1-REBUILD"
```

The **output directory must not already exist**. This example deliberately does **not** reuse the existing successful `LAKI-V5.1-FULL-AUDIO-BUILD` folder. The program refuses to overwrite an earlier stage or IMG.

To check the **already built** file, without rebuilding it:

```powershell
Get-FileHash "C:\LakiBox-Backup\LAKI-V5.1-FULL-AUDIO-BUILD\LAKI-Hybrid-V5.1-FULL-X96-AUDIO-V4.1-UNTESTED.img" -Algorithm SHA256
```

This should return the SHA-256 displayed at the top of this page for the known November 1 build. A future freshly packed image might receive a different top-level hash; compare its JSON report and provenance before interpreting a mismatch.

## Tests — no firmware blobs needed

```powershell
py -3 -m unittest discover -s tests -v
```

These tests check manifest safety, expected payload differences, hash refusal behavior and the mandatory local DTB reference. They **do not** demonstrate that the published script builds on the Windows host or that the result boots on physical LAKI hardware. The independently validated eARC patch in the original local test kit was compared byte-for-byte with the public version while preparing this update.

## Safety limitations

- **V4.1** was tested on one already modified LAKI M6CW4K and had functional IPTV video and analog AUX sound at an adequate Android `STREAM_MUSIC` volume. See [V4.1 audio notes](V4_1_AUDIO.md).
- **V5.1 FULL AUDIO has never been boot-tested or clean-flash-tested**. Its Bluetooth first-boot permission handling is also unverified on a clean device.
- This **FULL** image contains an explicit X96 `PARTITION/bootloader` manifest entry. An early bootloader/DDR mismatch can brick an untouched Orion LAKI or other board revision; the successful V4.1 box already had an X96 bootloader. Read [flashing risks](FLASHING.md).
- The scripts never flash a device, grant Android permissions, or overwrite the input images. They only work on files on the operator's computer.
- Do not redistribute the prebuilt IMG or proprietary DTB/kernel/vendor/bootloader blobs without checking the rights for each component. The repo provides only our original scripts and documentation.

**The existence of V5.1 FULL does not make V5.1 NOBOOTLOADER available**. That would require a separately built and independently verified output, and the name alone is not a bootloader-safety guarantee.
