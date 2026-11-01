#!/usr/bin/env bash
# LAKI V6: Bluetooth default-permission XML + model/brand/build ID in ONE staging ext4 pass.
set -Eeuo pipefail
if (( $# != 5 )); then
  echo 'Usage: patch_v6_system_identity.sh STAGED_SYSTEM_PARTITION BT_XML FRESH_WORKDIR LIMIT_BYTES PROP_HELPER' >&2
  exit 2
fi
image=$1; xml=$2; work=$3; limit=$4; prop_helper=$5
fail(){ echo "STOP: $*" >&2; exit 4; }
for program in simg2img img2simg debugfs e2fsck python3 cmp cp mv stat awk grep sed dd od head; do
  command -v "$program" >/dev/null || fail "Missing WSL dependency: $program"
done
[[ -f "$image" ]] || fail "Missing staged partition: $image"
[[ -f "$xml" && -f "$prop_helper" ]] || fail 'Missing XML or property patch helper'
[[ ! -e "$work" ]] || fail 'Work directory exists; use fresh output root'
[[ "$work" != *' '* && "$image" != *' '* ]] || fail 'Staging paths containing spaces are unsupported by debugfs; aborting'
[[ $limit =~ ^[0-9]+$ ]] || fail 'Invalid partition limit'
mkdir -p "$work"
raw="$work/system.raw.ext4"
magic=$(head -c4 "$image" | od -An -tx1 | tr -d ' \n')
if [[ "$magic" == '3aff26ed' ]]; then
  simg2img "$image" "$raw"
  sparse=1
else
  cp -- "$image" "$raw"
  sparse=0
fi
size=$(stat -c '%s' "$raw")
(( size >= 10485760 && size <= limit )) || fail "Unexpected raw ext4 size $size; cap $limit"
sb=$(dd if="$raw" bs=1 skip=1080 count=2 status=none | od -An -tx1 | tr -d ' \n')
[[ "$sb" == '53ef' ]] || fail 'Not an ext4 image (superblock magic mismatch)'

# Find the build.prop actually containing the three donor identifiers.
found=''
for candidate in /build.prop /system/build.prop; do
  info=$(debugfs -R "stat $candidate" "$raw" 2>/dev/null || true)
  if grep -q 'Inode:' <<< "$info"; then
    dumped="$work/$(echo "$candidate" | tr '/' '_').orig"
    debugfs -R "dump $candidate $dumped" "$raw" >/dev/null 2>&1 || fail "Could not dump $candidate"
    if grep -q '^ro.product.model=' "$dumped"; then
      [[ -z "$found" ]] || fail 'Multiple build.prop files contain ro.product.model; refusing ambiguous patch'
      found=$candidate
      original=$dumped
      original_info=$info
    fi
  fi
done
[[ -n "$found" ]] || fail 'Did not find a build.prop containing ro.product.model; no modification made'

# Preserve EXACT input permissions rather than imposing 0644.
# The previously observed LAKI V5.1 build.prop used root:root, mode 0600, SELinux system_file.
# Other expected donor variants may use 0644. Reject anything else.
original_mode=$(sed -nE 's/.*Mode:[[:space:]]+([0-7]{4})[[:space:]].*/\1/p' <<< "$original_info" | head -n1)
[[ "$original_mode" == '0600' || "$original_mode" == '0644' ]] || fail "Unexpected build.prop mode: $original_mode; expected 0600 or 0644"
grep -Eq 'Type:[[:space:]]+regular' <<< "$original_info" || fail 'build.prop is not a regular file'
original_uid=$(sed -nE 's/.*User:[[:space:]]*([0-9]+).*/\1/p' <<< "$original_info" | head -n1)
original_gid=$(sed -nE 's/.*Group:[[:space:]]*([0-9]+).*/\1/p' <<< "$original_info" | head -n1)
[[ "$original_uid" == '0' && "$original_gid" == '0' ]] || fail 'build.prop is not owned by root:root'
# Inspect the canonical 'debugfs stat' extended-attribute listing, not ea_list,
# because the latter may format its output differently on WSL distributions.
attr_names=$(printf '%s\n' "$original_info" | sed -nE 's/^[[:space:]]+([a-zA-Z0-9_.-]+)[[:space:]]+\([0-9]+\)[[:space:]]*=.*/\1/p')
if grep -q '^Extended attributes:' <<< "$original_info"; then
  [[ "$attr_names" == 'security.selinux' ]] || fail "Unknown or unparseable build.prop extended attributes: $attr_names"
else
  [[ -z "$attr_names" ]] || fail 'Unexpected attributes detected'
fi
if [[ "$attr_names" == 'security.selinux' ]]; then
  debugfs -R "ea_get -f $work/selinux.attr $found security.selinux" "$raw" >/dev/null 2>&1 || fail 'Failed to preserve SELinux label'
  [[ -s "$work/selinux.attr" ]] || fail 'Empty SELinux attribute'
  python3 - "$work/selinux.attr" <<'PYSEL'
from pathlib import Path
import sys
label=Path(sys.argv[1]).read_bytes().rstrip(b'\x00')
if label != b'u:object_r:system_file:s0':
    raise SystemExit('Refusing unknown build.prop SELinux context')
PYSEL
fi
python3 "$prop_helper" "$original" "$work/build.prop.new" || fail 'Property checks failed; source is not expected Magicsee 152F donor'

# Check default permissions path before any filesystem write.
# Magicsee source must NOT already have our XML. V6 must never silently overwrite it.
xml_target=/etc/default-permissions/laki-bluetooth.xml
if debugfs -R "stat $xml_target" "$raw" 2>/dev/null | grep -q 'Inode:'; then
  fail "Bluetooth XML already exists in donor system: $xml_target"
fi
xml_dir=/etc/default-permissions
has_xml_dir=0
if debugfs -R "stat $xml_dir" "$raw" 2>/dev/null | grep -q 'Inode:'; then
  has_xml_dir=1
fi
# Preserve a pinned SELinux context for new system file if original build.prop has one.
if [[ "$attr_names" == 'security.selinux' ]]; then
  cp "$work/selinux.attr" "$work/xml.selinux.attr"
else
  printf 'u:object_r:system_file:s0\0' > "$work/xml.selinux.attr"
fi

# Only modify the COPY of system.PARTITION. The source IMG is SHA-pinned and untouched.
debugfs -w -R "rm $found" "$raw" >/dev/null 2>&1 || fail 'Could not remove old build.prop from staged image'
debugfs -w -R "write $work/build.prop.new $found" "$raw" >/dev/null 2>&1 || fail 'Could not write patched build.prop'
debugfs -w -R "set_inode_field $found mode 010${original_mode}" "$raw" >/dev/null 2>&1 || fail 'Could not set file mode'
debugfs -w -R "set_inode_field $found uid 0" "$raw" >/dev/null 2>&1 || fail 'Could not set owner'
debugfs -w -R "set_inode_field $found gid 0" "$raw" >/dev/null 2>&1 || fail 'Could not set group'
if [[ -n "$attr_names" ]]; then
  debugfs -w -R "ea_set -f $work/selinux.attr $found security.selinux" "$raw" >/dev/null 2>&1 || fail 'Could not restore SELinux context'
  debugfs -R "ea_get -f $work/selinux.after $found security.selinux" "$raw" >/dev/null 2>&1 || fail 'Could not read restored SELinux context'
  cmp "$work/selinux.attr" "$work/selinux.after" || fail 'SELinux label changed'
fi
newinfo=$(debugfs -R "stat $found" "$raw" 2>/dev/null)
grep -Eq "Mode:[[:space:]]+${original_mode}[[:space:]]" <<< "$newinfo" || fail 'Resulting build.prop mode differs from original'
new_uid=$(sed -nE 's/.*User:[[:space:]]*([0-9]+).*/\1/p' <<< "$newinfo" | head -n1)
new_gid=$(sed -nE 's/.*Group:[[:space:]]*([0-9]+).*/\1/p' <<< "$newinfo" | head -n1)
[[ "$new_uid" == "$original_uid" && "$new_gid" == "$original_gid" ]] || fail 'Resulting build.prop owner differs from original'
new_attrs=$(printf '%s\n' "$newinfo" | sed -nE 's/^[[:space:]]+([a-zA-Z0-9_.-]+)[[:space:]]+\([0-9]+\)[[:space:]]*=.*/\1/p')
[[ "$new_attrs" == "$attr_names" ]] || fail 'Resulting build.prop extended attributes differ from original' 
debugfs -R "dump $found $work/build.prop.verified" "$raw" >/dev/null 2>&1 || fail 'Cannot read back modified file'
cmp "$work/build.prop.new" "$work/build.prop.verified" || fail 'Property read-back mismatch'

# Add Bluetooth default permission in SAME staged ext4 conversion.
if (( !has_xml_dir )); then
  debugfs -w -R "mkdir $xml_dir" "$raw" >/dev/null 2>&1 || fail 'Cannot create default-permissions folder'
  debugfs -w -R "set_inode_field $xml_dir mode 040755" "$raw" >/dev/null 2>&1 || fail 'Cannot set new default-permissions directory mode'
  debugfs -w -R "set_inode_field $xml_dir uid 0" "$raw" >/dev/null 2>&1 || fail 'Cannot set new default-permissions directory owner'
  debugfs -w -R "set_inode_field $xml_dir gid 0" "$raw" >/dev/null 2>&1 || fail 'Cannot set new default-permissions directory group'
  debugfs -w -R "ea_set -f $work/xml.selinux.attr $xml_dir security.selinux" "$raw" >/dev/null 2>&1 || fail 'Cannot label new default-permissions directory'
fi
# debugfs write takes unquoted single-token paths; workdir is checked to have no spaces.
cp -- "$xml" "$work/xml.source"
debugfs -w -R "write $work/xml.source $xml_target" "$raw" >/dev/null 2>&1 || fail 'Cannot write Bluetooth XML'
debugfs -w -R "set_inode_field $xml_target mode 0100644" "$raw" >/dev/null 2>&1 || fail 'Cannot set Bluetooth XML mode'
debugfs -w -R "set_inode_field $xml_target uid 0" "$raw" >/dev/null 2>&1 || fail 'Cannot set Bluetooth XML owner'
debugfs -w -R "set_inode_field $xml_target gid 0" "$raw" >/dev/null 2>&1 || fail 'Cannot set Bluetooth XML group'
debugfs -w -R "ea_set -f $work/xml.selinux.attr $xml_target security.selinux" "$raw" >/dev/null 2>&1 || fail 'Cannot set Bluetooth XML SELinux context'
debugfs -R "dump $xml_target $work/xml.verified" "$raw" >/dev/null 2>&1 || fail 'Cannot read Bluetooth XML'
cmp "$xml" "$work/xml.verified" || fail 'Bluetooth XML differs on read-back'
xml_info=$(debugfs -R "stat $xml_target" "$raw" 2>/dev/null)
grep -Eq 'Mode:[[:space:]]+0644[[:space:]]' <<< "$xml_info" || fail 'Bluetooth XML permissions not 0644'
grep -Eq 'User:[[:space:]]+0[[:space:]]+Group:[[:space:]]+0' <<< "$xml_info" || fail 'Bluetooth XML owner not root:root'
debugfs -R "ea_get -f $work/xml.selinux.after $xml_target security.selinux" "$raw" >/dev/null 2>&1 || fail 'Cannot read Bluetooth XML SELinux context'
cmp "$work/xml.selinux.attr" "$work/xml.selinux.after" || fail 'Bluetooth XML SELinux context mismatch'

# ext4 consistency check. e2fsck exit 1 means fixed metadata.
set +e
e2fsck -fy "$raw" >"$work/e2fsck.log" 2>&1
rc=$?
set -e
(( rc == 0 || rc == 1 )) || { tail -n 40 "$work/e2fsck.log" >&2; fail "e2fsck exited $rc"; }
debugfs -R "dump $found $work/build.prop.after-fsck" "$raw" >/dev/null 2>&1 || fail 'Cannot read build.prop after fsck'
cmp "$work/build.prop.new" "$work/build.prop.after-fsck" || fail 'fsck altered build.prop'
debugfs -R "dump $xml_target $work/xml.after-fsck" "$raw" >/dev/null 2>&1 || fail 'Cannot read Bluetooth XML after fsck'
cmp "$xml" "$work/xml.after-fsck" || fail 'fsck altered Bluetooth XML'
if (( sparse )); then
  img2simg "$raw" "$work/system.new.PARTITION"
  simg2img "$work/system.new.PARTITION" "$work/system.roundtrip.raw"
  cmp "$raw" "$work/system.roundtrip.raw" || fail 'Sparse round-trip does not match'
else
  cp "$raw" "$work/system.new.PARTITION"
fi
[[ -s "$work/system.new.PARTITION" ]] || fail 'No output partition'
# Replace only the staging COPY after ALL checks passed.
mv -f "$work/system.new.PARTITION" "$image"
echo "PASS: V6 Bluetooth XML + identity patched in staged system.PARTITION; metadata and readback verified"
