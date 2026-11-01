# Changelog and validation record

## V5.1 FULL AUDIO — one-device hardware validation (2026-11-01)

- Operator reported a successful physical USB flash and Android boot using the locally built V5.1 FULL AUDIO image (SHA-256 `B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378`).
- Flash options reportedly included **erase user data and erase bootloader**; option selection is not an independent bootloader readback.
- **PASS:** Wi-Fi and Internet, Bluetooth discovery/pairing, Bluetooth audio, IPTV video without freezing, analog AUX audio and normal reboot.
- Hardware: **one previously X96-modified Orion LAKI M6CW4K (S905X3/AC213)**; untouched stock bootloader, other revisions and long-term stability not verified.
- Bluetooth permission auto-grant mechanism not independently inspected; only functional pairing/audio were confirmed.
- The earlier, different V5 NOBOOTLOADER and V5 FULL images remain **offline-only**, as does the proposed V6 builder until independently built/tested.
- See [full hardware-validation record](docs/V5_1_HARDWARE_VALIDATION_2026-11-01.md).

## V5.1 FULL AUDIO — built and SHA-256 verified offline (2026-11-01)

- Combines the offline-verified V5 FULL X96 image with the physically tested V4.1 eARC-off `boot.PARTITION` and `_aml_dtb.PARTITION`.
- The new public scripts independently recalculate and verify the constrained eARC patch from a **locally supplied** SHA-256-pinned DTB; no binary DTB is committed.
- Local pack/unpack and per-partition checks passed; only two audio partitions changed; `system` and `vendor` unchanged from V5 FULL.
- A separate `Get-FileHash` confirmed the packed-image SHA-256: `B4D2CD269AB8516F123111DB5A234317A258C3D3835AA945EF7A6CED04D8A378`.
- **Historical status at the moment of offline build; superseded by the separate V5.1 physical test reported above.** Stock-Orion-bootloader compatibility is still unverified.
- Published source is a slight packaging adaptation of the original build kit (local `--reference-dtb` input), not a new Windows end-to-end rerun.

## V5 FULL — build completed, offline only (2026-11-01)

- Copied already offline-verified V5 files without changing their payloads.
- Used X96 `DDR.USB` and `aml_sdc_burn.UBOOT` matching documented SHA-256 fingerprints.
- Restored one `PARTITION/bootloader` record to `image.cfg`.
- `AmlImagePack -r` succeeded; subsequent `-d` succeeded; payload SHA-256 checks passed.
- Output hash: `AE80E1F705952FB04C3B21C7F4F2E57486FA45E0B2105282CDF70DCDC6D790F9`.
- **Not yet flashed on the first or second physical box.**

## V5 NOBOOTLOADER — build completed, offline only (2026-11-01)

- Created from the tested V4 staging input.
- Changed only the Android system image to include a default `READ_CONTACTS` grant exception.
- ext4 check, Amlogic pack/unpack and 12-file staging-vs-unpacked SHA-256 comparison passed.
- Original first version of the V5 builder required manual creation of the verification directory; the repository version adds that step automatically.
- Output hash: `900DCEF88826BEC6F77516788B5612022C338515E945E309CC41EDCE1631CD4B`.
- **Not boot-tested or factory-reset-tested on the device.**

## V4 — physically tested (2026-10-31 / 2026-11-01)

- Used previously working X96 USB boot components, adjusted AC213 DT, Magicsee kernel and matching Unisoc drivers/vendor userspace.
- Flash reached explicit `Burning successfully`.
- Boot, Wi-Fi connection, Bluetooth discovery, pairing, and speaker audio confirmed.
- Bluetooth Java crash fixed at runtime by `pm grant ... READ_CONTACTS` after identifying the PBAP permission exception.
- Original image hash: `D22AB3AAFBE71C9201360BA15762952C3CD94C0D14BE788AD8EE8B4D3FF200BF`.

## Documentation / scripts

- Contains community-authored build scripts only; proprietary ROM/kernel/bootloader/APK blobs are not provided.
- A syntax check of the scripts **does not** substitute for an end-to-end build test with original Windows source files.
