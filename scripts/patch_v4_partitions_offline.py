#!/usr/bin/env python3
"""OFFLINE patch LAKI Hybrid V4 Amlogic dtb and boot.PARTITION (no flash).

Only for verified Android v0 boot images containing an identical gzipped AML multi-DTB
as _aml_dtb.PARTITION. The selected DTB must have audio subtree matching the
supplied live V4 snapshot AND the expected LAKI V4 Wi-Fi / BT settings.
Usage:
  python patch_v4_partitions_offline.py --source LEVEL1_UNPACK_DIR --out OUTPUT_DIR --reference-dtb LOCAL_V4_RUNNING.dtb
Source requires files: boot.PARTITION and _aml_dtb.PARTITION.
"""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
from patch_laki_earc import parse,patch

LIVE_SHA='5d3902b74ad206078503051c858be97963b7307f21d102c20a078c75e5a900fc'
TARGET_ID=b'sm1_ac213_2g\0'

def sha(b):return hashlib.sha256(b).hexdigest()
def unpack_fdt_slot(slot):
    if len(slot)<40: raise ValueError('Too short')
    total=struct.unpack_from('>I',slot,4)[0]
    tree=parse(slot[:total])
    return slot[:total],slot[total:],tree

def get_prop(t,path,p):
    x=t['props'].get((path,p))
    return x[4] if x else None

def verify_expected_v4(tree,live):
    if get_prop(tree,'/','amlogic-dt-id') != TARGET_ID:
        raise ValueError('This is not sm1_ac213_2g')
    for p in ['/auge_sound','/t9015','/soc/bus@ff663000/earc@0']:
        paths=[x for x in live['nodes'] if x==p or (p=='/auge_sound' and x.startswith(p+'/'))]
        for x in paths:
            if x not in tree['nodes']: raise ValueError(f'Audio node {x} missing')
            xprops={k[1]:v[4] for k,v in live['props'].items() if k[0]==x}
            yprops={k[1]:v[4] for k,v in tree['props'].items() if k[0]==x}
            if xprops != yprops: raise ValueError(f'Audio node properties differ at {x}; not the tested V4 audio setup')
    for path,prop in [('/wifi','interrupt_pin'),('/wifi','irq_trigger_type'),('/bt-dev','gpio_reset')]:
        if get_prop(tree,path,prop)!=get_prop(live,path,prop):
            raise ValueError(f'{path}/{prop} differs from current V4')
    if get_prop(tree,'/bt-dev','gpio_en') is not None:
        raise ValueError('Found old X96 BT gpio_en, not V4')

def aml_entries(raw):
    if len(raw)<2048 or raw[:4]!=b'AML_': raise ValueError('Not AML multi-DTB')
    version,count=struct.unpack_from('<II',raw,4)
    if version!=2 or count!=4: raise ValueError(f'Unexpected AML multi-DTB version/count {version}/{count}')
    spans=[]
    for i in range(count):
        off,length=struct.unpack_from('<II',raw,12+i*56+48)
        if off<12+56*count or off+length>len(raw) or off%4:
            raise ValueError('Invalid multi-DTB slot')
        spans.append((i,off,length))
    if any(a[1]+a[2]>b[1] for a,b in zip(sorted(spans,key=lambda x:x[1]),sorted(spans,key=lambda x:x[1])[1:])):
        raise ValueError('Overlapping multi-DTB slots')
    return spans

def patch_multi(gz,live):
    if not gz.startswith(b'\x1f\x8b'):raise ValueError('Missing gzip header')
    raw=gzip.decompress(gz)
    positions=[]
    for i,off,length in aml_entries(raw):
        slot=raw[off:off+length]
        try: data,padding,tree=unpack_fdt_slot(slot)
        except Exception as exc: raise ValueError(f'Bad FDT in slot {i}: {exc}')
        if get_prop(tree,'/','amlogic-dt-id')==TARGET_ID:
            verify_expected_v4(tree,live)
            patched,change=patch(data)
            if len(patched)!=len(data): raise ValueError('FDT span changed')
            after = parse(patched)
            if get_prop(after,'/soc/bus@ff663000/earc@0','status')!=b'disabled\0': raise ValueError('Status patch failed')
            positions.append((i,off,length,patched+padding))
    if len(positions)!=1:raise ValueError(f'Expected 1 matching DTB slot, got {len(positions)}')
    output=bytearray(raw)
    for i,off,length,payload in positions:output[off:off+length]=payload
    out=gzip.compress(bytes(output),mtime=0)
    if len(gzip.decompress(out))!=len(raw):raise ValueError('Wrong unpack size')
    for j,o,n in aml_entries(raw):
        before=raw[o:o+n]
        after=gzip.decompress(out)[o:o+n]
        if j!=positions[0][0] and before!=after: raise ValueError(f'Other board variant changed: {j}')
    return out,positions[0][0]

def read_boot_second(b):
    if len(b)<2048 or b[:8]!=b'ANDROID!':raise ValueError('Not Android boot image')
    k,r,s=[struct.unpack_from('<I',b,o)[0] for o in (8,16,24)]
    page,dt = struct.unpack_from('<I',b,36)[0],struct.unpack_from('<I',b,40)[0]
    # Offset 40 is header_version on Android boot v1; some Amlogic images set it to 1.
    if page not in (2048,4096) or r!=0 or dt not in (0,1) or k<1000000 or s<1000:
        raise ValueError('Unexpected boot layout, refuse to modify')
    second_at=page+((k+page-1)//page)*page
    if second_at+s>len(b):raise ValueError('Second stage truncated')
    original_second=b[second_at:second_at+s]
    original_id=hashlib.sha1(b[page:page+k]+struct.pack('<I',k)+struct.pack('<I',0)+original_second+struct.pack('<I',s)+struct.pack('<I',0)).digest()
    if original_id!=b[576:596]:raise ValueError('Android boot v0 SHA1 is invalid; refusing')
    return k,r,s,page,second_at,original_second

def change_boot(b,old_dtb,new_dtb):
    k,r,s,page,at,second=read_boot_second(b)
    if gzip.decompress(second)!=gzip.decompress(old_dtb):
        raise ValueError('Boot embedded DTB differs from standalone DTB. Refusing silent replacement')
    if len(b)%page!=0:
        raise ValueError('Unexpected boot partition layout')
    old_used=at+((s+page-1)//page)*page
    if any(b[old_used:]):
        raise ValueError('Non-zero boot data after second stage; refusing to discard it')
    new=bytearray(b[:at]);new.extend(new_dtb)
    new.extend(b'\0'*((-len(new))%page))
    # Retain original boot partition-file length when possible; never silently truncate it.
    if len(new)<len(b):new.extend(b'\0'*(len(b)-len(new)))
    struct.pack_into('<I',new,24,len(new_dtb))
    digest=hashlib.sha1(b[page:page+k]+struct.pack('<I',k)+struct.pack('<I',0)+new_dtb+struct.pack('<I',len(new_dtb))+struct.pack('<I',0)).digest()
    new[576:596]=digest
    nr=read_boot_second(bytes(new))
    if gzip.decompress(nr[5])!=gzip.decompress(new_dtb):raise ValueError('Boot second stage check failed')
    return bytes(new)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reference-dtb',type=Path,required=True,help='Local original V4 running DTB; not published')
    a=p.parse_args()
    src=a.source.resolve();out=a.out.resolve()
    if src==out or src in out.parents or out in src.parents:
        raise SystemExit('Output must be a separate directory (not inside source)')
    if out.exists():
        raise SystemExit('Output directory already exists. Choose a fresh directory')
    boot=(src/'boot.PARTITION').read_bytes()
    gz=(src/'_aml_dtb.PARTITION').read_bytes()
    live=a.reference_dtb.resolve().read_bytes()
    if sha(live)!=LIVE_SHA:raise ValueError('Local running DTB SHA256 mismatch')
    live_tree=parse(live)
    patched,index=patch_multi(gz,live_tree)
    newboot=change_boot(boot,gz,patched)
    out.mkdir(parents=True)
    (out/'boot.PARTITION').write_bytes(newboot)
    (out/'_aml_dtb.PARTITION').write_bytes(patched)
    report={'message':'OFFLINE TEST ONLY. Not a flashable image. Never write these partitions directly with dd.',
            'source':str(src),'target_board_slot':index,
            'original_boot_sha256':sha(boot),'modified_boot_sha256':sha(newboot),
            'original_dtb_partition_sha256':sha(gz),'modified_dtb_partition_sha256':sha(patched),
            'other_board_variants_unchanged':True,'boot_header_sha1_recomputed_and_verified':True,
            'no_changes_to_bootloader_system_vendor_data':True,
            'video_hdmi_mode_not_modified':True}
    (out/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
