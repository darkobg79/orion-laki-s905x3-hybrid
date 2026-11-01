#!/usr/bin/env python3
"""Pinned AC213 2G Wi-Fi IRQ / Bluetooth GPIO patch from the original V4 workflow.

No firmware blobs are embedded. Input must match the known X96 Plus 5 DTB.
Import helpers from build_laki_v6.py. No direct flashing or file writing.
"""
import argparse, gzip, io, hashlib, shutil, struct, json
from pathlib import Path

X96_DDR_SHA = '77cb764b897f59d146178513cc3563eb1499a06f3dcccb93a3f405c16f999d33'
X96_BURN_SHA = '8be0c10af6d8fa087abceacd7f09d0aa16356b508ede647e08cde1e5a4ed0e45'

def check(ok, msg):
    if not ok: raise ValueError(msg)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def b32(buf, offset): return struct.unpack_from('>I', buf, offset)[0]
def set_b32(buf, offset, val): struct.pack_into('>I', buf, offset, val)

def fdt_properties(blob):
    hdr = struct.unpack_from('>10I', blob, 0)
    check(hdr[0] == 0xd00dfeed and hdr[1] <= len(blob), 'DTB magic/size invalid')
    off_struct, off_strings, size_strings, size_struct = hdr[2], hdr[3], hdr[8], hdr[9]
    strings = blob[off_strings:off_strings+size_strings]
    offset=off_struct; stack=[]; props={}; nodes={}
    while offset < off_struct+size_struct:
        token=b32(blob,offset);offset+=4
        if token == 1:
            end=blob.index(0,offset)
            name=blob[offset:end].decode('utf-8','replace')
            offset=(end+4)&~3
            stack.append(name)
            nodes['/'+'/'.join(n for n in stack if n)]=True
        elif token == 2: stack.pop()
        elif token == 3:
            size=b32(blob,offset); nameoff=b32(blob,offset+4)
            check(nameoff < len(strings),'DTB property name offset outside string table')
            end=strings.index(0,nameoff)
            name=strings[nameoff:end].decode('ascii','replace')
            value_off=offset+8
            props[('/'+'/'.join(n for n in stack if n),name)]=(value_off,size,offset,offset+4)
            offset=(value_off+size+3)&~3
        elif token==4: pass
        elif token==9: break
        else: raise ValueError('Invalid DTB token %d' % token)
    return hdr,props

def patch_fdt(dtb):
    hdr,props=fdt_properties(dtb)
    d=bytearray(dtb)
    def get(path,key):
        off,n,_,_=props[(path,key)]
        return bytes(d[off:off+n])
    check(get('/','amlogic-dt-id') == b'sm1_ac213_2g\x00', 'Not the AC213 2GB Device Tree')
    check(get('/wifi','interrupt_pin') == struct.pack('>3I',0x19,0x49,0), 'Unexpected wifi IRQ GPIO')
    check(get('/wifi','irq_trigger_type') == b'GPIO_IRQ_LOW\0','Unexpected wifi IRQ polarity')
    check(get('/bt-dev','gpio_en') == struct.pack('>3I',0x19,0x53,0), 'Unexpected bt gpio')
    # Change values in the existing structure without moving it.
    off,_,_,_=props['/wifi','interrupt_pin']
    set_b32(d,off+4,0x54)
    off,old_len,prop_off,_=props['/wifi','irq_trigger_type']
    check(d[off+old_len:off+16]==b'\0'*(16-old_len),'No room for 14-byte HIGH value')
    new_value=b'GPIO_IRQ_HIGH\0'
    d[off:off+len(new_value)]=new_value
    set_b32(d,prop_off,len(new_value))
    # Retarget gpio_en property name to gpio_reset. Append name to DTB's spare
    # zero padding AFTER its existing string table; keep DTB slot size unchanged.
    name=b'gpio_reset\x00'
    name_pos=hdr[3]+hdr[8]
    check(hdr[1]+len(name) <= len(d),'No padding space in Device Tree')
    check(d[name_pos:name_pos+len(name)]==b'\x00'*len(name),'No zero padding at DTB string tail')
    d[name_pos:name_pos+len(name)]=name
    _,_,_,name_offset_loc=props['/bt-dev','gpio_en']
    set_b32(d,name_offset_loc,hdr[8])
    set_b32(d,4,hdr[1]+len(name))
    set_b32(d,32,hdr[8]+len(name))
    _,new_props=fdt_properties(d)
    check(('/bt-dev','gpio_reset') in new_props and ('/bt-dev','gpio_en') not in new_props,'BT rename failed')
    check(bytes(d[new_props['/wifi','irq_trigger_type'][0]:new_props['/wifi','irq_trigger_type'][0]+14])==new_value,'IRQ polarity patch failed')
    # Preserve eMMC configuration exactly, and every FDT outside selected 3 prop locations.
    return bytes(d)

def stable_gzip(raw: bytes) -> bytes:
    """Build a reproducible gzip wrapper across CPython 3.11--3.13.

    gzip.compress(mtime=0) historically sometimes delegates to zlib and
    uses OS=3 (Unix) instead of OS=255. The DTB bytes are identical after
    decompressing, but SHA-256 is different, so pinned verification fails.

    GzipFile writes OS=255 and a deterministic zero-time header on both
    Windows and Linux. We still REQUIRE the historical SHA-256 of the output
    in build_laki_v6.py. No check is bypassed.
    """
    with io.BytesIO() as stream:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=9,
                           mtime=0, fileobj=stream) as writer:
            writer.write(raw)
        packed = stream.getvalue()
    if packed[:10] != bytes.fromhex('1f8b08000000000002ff'):
        raise ValueError('Noncanonical gzip header: ' + packed[:10].hex())
    if gzip.decompress(packed) != raw:
        raise ValueError('Canonical gzip roundtrip mismatch')
    return packed

def patch_multi_dtb(packed):
    check(packed.startswith(b'\x1f\x8b'), 'Expect gzipped AML multi-DTB')
    raw=gzip.decompress(packed)
    check(raw[:4]==b'AML_', 'Expect AML multi-DTB wrapper')
    version,count=struct.unpack_from('<II',raw,4)
    check(version==2 and 1<=count<=30, 'Unsupported AML multi-DTB structure')
    entries=[]; replaced=[]; out=bytearray(raw)
    for i in range(count):
        pos=12+i*56
        labels=[raw[pos+j*16:pos+(j+1)*16].split(b'\0')[0].decode('ascii','replace').strip() for j in range(3)]
        off,length=struct.unpack_from('<II',raw,pos+48)
        check(off+length<=len(raw),'Bad DTB entry offset')
        content=raw[off:off+length]
        h,props=fdt_properties(content)
        path=('/','amlogic-dt-id')
        dtid=content[props[path][0]:props[path][0]+props[path][1]].rstrip(b'\0').decode('ascii','replace') if path in props else 'unknown'
        entries.append({'index':i, 'board': dtid, 'labels':labels, 'bytes':length})
        if dtid=='sm1_ac213_2g':
            new=patch_fdt(content)
            check(len(new)==len(content),'FDT slot length changed')
            out[off:off+length]=new
            replaced.append(i)
    check(len(replaced)==1,'Expect exactly one sm1_ac213_2g DTB, found %d'%len(replaced))
    updated=stable_gzip(bytes(out))
    check(gzip.decompress(updated)==bytes(out),'gzip round-trip invalid')
    return updated, entries, replaced

def reassemble_boot(magic_boot, second):
    check(magic_boot[:8]==b'ANDROID!', 'Missing Android boot magic')
    ksize,rsize,old_second=struct.unpack_from('<III',magic_boot,8)[0],struct.unpack_from('<I',magic_boot,16)[0],struct.unpack_from('<I',magic_boot,24)[0]
    page=struct.unpack_from('<I',magic_boot,36)[0]
    check(page in (2048,4096) and rsize==0 and ksize>5000000, 'Unexpected Android boot layout')
    kernel=magic_boot[page:page+ksize]
    second_off=page+((ksize+page-1)//page)*page
    check(magic_boot[second_off:second_off+old_second].startswith(b'\x1f\x8b'), 'Magicsee boot second is not gzip DTB')
    # Verify original Android v0 boot header checksum before modifying it.
    calculated=hashlib.sha1(kernel+struct.pack('<I',ksize)+struct.pack('<I',0)+magic_boot[second_off:second_off+old_second]+struct.pack('<I',old_second)+struct.pack('<I',0)).digest()
    check(calculated==magic_boot[576:596], 'Magicsee boot SHA1 does not match')
    new=bytearray(magic_boot[:second_off]);new.extend(second)
    new.extend(bytes((-len(new))%page))
    struct.pack_into('<I',new,24,len(second))
    checksum=hashlib.sha1(kernel+struct.pack('<I',ksize)+struct.pack('<I',0)+second+struct.pack('<I',len(second))+struct.pack('<I',0)).digest()
    new[576:608]=checksum+bytes(12)
    check(bytes(new[page:page+ksize])==kernel, 'Kernel has been changed')
    check(len(new)<16777216,'Boot image too big')
    return bytes(new)

