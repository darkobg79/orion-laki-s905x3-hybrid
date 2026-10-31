#!/usr/bin/env bash
# Run inside WSL: patch ONLY a COPY of the Android 9 system.PARTITION.
set -Eeuo pipefail
if (( $# != 4 )); then
    echo "Usage: patch_system_partition.sh image xml workdir partition_limit_bytes" >&2
    exit 2
fi
image="$1"; xml="$2"; work="$3"; limit="$4"
for tool in debugfs e2fsck stat cmp cp mv grep awk; do
    command -v "$tool" >/dev/null || { echo "MISSING: $tool" >&2; exit 2; }
done
[[ -f "$image" && -f "$xml" ]] || { echo 'Image or XML missing' >&2; exit 2; }
[[ "$work" != *' '* ]] || { echo 'Workdir must have no spaces (debugfs limitation)' >&2; exit 2; }
[[ ! -e "$work" ]] || { echo "Workdir already exists, refusing to overwrite: $work" >&2; exit 2; }
mkdir -p "$work"
magic=$(head -c 4 "$image" | od -An -tx1 | tr -d ' \n')
raw="$work/system.raw.ext4"
case "$magic" in
  3aff26ed)
    command -v simg2img >/dev/null || { echo 'MISSING: simg2img (apt install android-sdk-libsparse-utils)' >&2; exit 2; }
    command -v img2simg >/dev/null || { echo 'MISSING: img2simg (apt install android-sdk-libsparse-utils)' >&2; exit 2; }
    echo '[1/5] Android sparse -> raw ext4'
    simg2img "$image" "$raw"
    sparse=1
    ;;
  *)
    echo '[1/5] Raw ext4 copy'
    cp "$image" "$raw"
    sparse=0
    ;;
esac
size=$(stat -c '%s' "$raw")
[[ "$size" -gt 10485760 && "$size" -le "$limit" ]] || { echo "Invalid/ext4-too-large reconstructed size: $size (limit $limit)" >&2; exit 3; }
# ext4 superblock starts at offset 1024; magic is at 1024+56=1080
sbmagic=$(dd if="$raw" bs=1 skip=1080 count=2 status=none | od -An -tx1 | tr -d ' \n')
[[ "$sbmagic" == '53ef' ]] || { echo 'NOT ext4: wrong superblock magic' >&2; exit 3; }
[[ -s "$work"/out.img ]] && { echo 'Unexpected existing output' >&2; exit 3; }
# debugfs emits warnings on stderr even when stat works; check actual Inode record.
if ! debugfs -R 'stat /etc/default-permissions' "$raw" 2>/dev/null | grep -q 'Inode:'; then
  echo '[2/5] Creating /etc/default-permissions in the ext4 filesystem'
  debugfs -w -R 'mkdir /etc/default-permissions' "$raw" >/dev/null
fi
if debugfs -R 'stat /etc/default-permissions/laki-bluetooth.xml' "$raw" 2>/dev/null | grep -q 'Inode:'; then
    echo 'Target file already exists; refusing to modify/overwrite' >&2
    exit 3
fi
cp "$xml" "$work/laki-bluetooth.xml"
echo '[3/5] Adding Android 9 default READ_CONTACTS runtime grant'
debugfs -w -R "write $work/laki-bluetooth.xml /etc/default-permissions/laki-bluetooth.xml" "$raw" >/dev/null
# Set deterministic Android system-file metadata (owner root:root, world-readable).
debugfs -w -R "set_inode_field /etc/default-permissions/laki-bluetooth.xml mode 0100644" "$raw" >/dev/null
debugfs -w -R "set_inode_field /etc/default-permissions/laki-bluetooth.xml uid 0" "$raw" >/dev/null
debugfs -w -R "set_inode_field /etc/default-permissions/laki-bluetooth.xml gid 0" "$raw" >/dev/null
# Verify file inside image matches the input exactly (including binary text).
debugfs -R "dump /etc/default-permissions/laki-bluetooth.xml $work/verified.xml" "$raw" >/dev/null 2>&1
cmp "$work/laki-bluetooth.xml" "$work/verified.xml" || { echo 'XML verification failed!' >&2; exit 4; }
statout=$(debugfs -R 'stat /etc/default-permissions/laki-bluetooth.xml' "$raw" 2>/dev/null)
printf '%s\n' "$statout" | grep -q 'Mode:  0644' || {
  echo 'WARNING: XML mode is not 0644; inspect the ext4 image before flashing' >&2
  printf '%s\n' "$statout" | head -n 8 >&2
  exit 4
}
echo '[4/5] Checking and repairing offline ext4 metadata'
set +e
e2fsck -fy "$raw"
rc=$?
set -e
[[ $rc -eq 0 || $rc -eq 1 ]] || { echo "e2fsck returned $rc; ABORT" >&2; exit 4; }
echo '[5/5] Converting modified ext4 back to source image format'
if (( sparse )); then
    img2simg "$raw" "$work/system.PARTITION.new"
else
    cp "$raw" "$work/system.PARTITION.new"
fi
[[ -s "$work/system.PARTITION.new" ]] || { echo 'Output is missing' >&2; exit 4; }
# Verify data after conversion by performing roundtrip for sparse images.
if (( sparse )); then
    simg2img "$work/system.PARTITION.new" "$work/system.check.raw.ext4"
    cmp "$raw" "$work/system.check.raw.ext4" || { echo 'Sparse roundtrip comparison FAILED' >&2; exit 5; }
    rm "$work/system.check.raw.ext4"
fi
# Output replaces only COPY of stage image, after all checks.
mv "$work/system.PARTITION.new" "$image"
rm -f "$raw" "$work/laki-bluetooth.xml" "$work/verified.xml"
echo 'SUCCESS: system.PARTITION patched in staging copy; source V4 untouched.'
