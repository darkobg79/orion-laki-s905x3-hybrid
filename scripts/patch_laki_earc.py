#!/usr/bin/env python3
"""Offline-only minimal FDT patch: disable broken eARC and remove the eARC DAI link.

Preserves FDT header, offsets, strings, and total length exactly. Does NOT flash anything.
Usage: python patch_laki_earc.py input-running.dtb output-earc-off.dtb
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

FDT_BEGIN_NODE, FDT_END_NODE, FDT_PROP, FDT_NOP, FDT_END = 1, 2, 3, 4, 9
EARC = '/soc/bus@ff663000/earc@0'
LINK = '/auge_sound/aml-audio-card,dai-link@6'

def align4(n): return (n+3)&~3

def parse(data):
    if len(data) < 40:
        raise ValueError('File too small')
    h = struct.unpack_from('>10I', data)
    magic, total, soff, stroff, rsv, ver, last, boot, strsize, structsize = h
    if magic != 0xd00dfeed or len(data) != total or ver < 16 or soff+structsize > total or stroff+strsize > total:
        raise ValueError('Invalid FDT header / size; refusing to patch')
    st = data[stroff:stroff+strsize]
    pos, stack, nodes, props, labels, ended = soff, [], {}, {}, {}, False
    while pos < soff + structsize:
        start = pos
        tok = struct.unpack_from('>I', data, pos)[0]; pos += 4
        if tok == FDT_BEGIN_NODE:
            end = data.index(b'\0', pos, soff+structsize)
            name = data[pos:end].decode('ascii', errors='strict'); pos = align4(end+1)
            stack.append(name)
            key = '/'+'/'.join(x for x in stack if x)
            nodes[key] = [start,None]
        elif tok == FDT_END_NODE:
            if not stack: raise ValueError('Unbalanced tree')
            key = '/'+'/'.join(x for x in stack if x)
            nodes[key][1] = pos
            stack.pop()
        elif tok == FDT_PROP:
            plen, nameoff = struct.unpack_from('>2I', data, pos); pos += 8
            if nameoff >= strsize: raise ValueError('Invalid string offset')
            nend = st.find(b'\0', nameoff)
            if nend < 0: raise ValueError('Invalid string')
            pname = st[nameoff:nend].decode('ascii',errors='strict')
            valstart = pos; pos += align4(plen)
            if pos > soff+structsize: raise ValueError('Property exceeds struct block')
            key = '/'+'/'.join(x for x in stack if x)
            props[(key,pname)] = (start,pos,valstart,plen,data[valstart:valstart+plen])
        elif tok == FDT_NOP:
            pass
        elif tok == FDT_END:
            ended = True
            if stack: raise ValueError('Unclosed tree')
            if pos != soff+structsize:
                raise ValueError('Unexpected data after FDT_END')
            break
        else: raise ValueError(f'Invalid token {tok} at {start}')
    if not ended: raise ValueError('Missing FDT_END')
    return {'header':h,'nodes':nodes,'props':props}

def hexsha(data): return hashlib.sha256(data).hexdigest()

def patch(data):
    pre = parse(data)
    nodes, props = pre['nodes'],pre['props']
    if LINK not in nodes or EARC not in nodes:
        raise ValueError('Expected LAKI V4 nodes not found; refusing')
    status = props.get((EARC,'status'))
    if not status or status[4] != b'okay\0':
        raise ValueError('Expected active eARC with status="okay"; refusing')
    cpu = props.get((LINK+'/cpu','sound-dai'))
    ep = props.get((EARC,'phandle'))
    if not cpu or not ep or len(cpu[4]) != 4 or cpu[4] != ep[4]:
        raise ValueError('eARC DAI phandle reference mismatch; refusing')
    root_hdr = pre['header']
    s, e, vs, oldlen, _ = status
    link_s, link_e = nodes[LINK]
    if not (s<e<=link_s<link_e):
        raise ValueError('Unexpected ordering; refusing')
    # Grow status property by one 32-bit word; recover that word from removed DAI-link NOPs.
    new_status = data[s:s+4]+struct.pack('>I',9)+data[s+8:s+12]+b'disabled\0'+b'\0'*3
    assert len(new_status)==e-s+4
    removed_len = link_e-link_s
    if removed_len%4 or removed_len<8: raise ValueError('Invalid node span')
    nops = struct.pack('>I',FDT_NOP)*((removed_len-4)//4)
    patched = data[:s]+new_status+data[e:link_s]+nops+data[link_e:]
    if len(patched) != len(data): raise ValueError('Length changed')
    post = parse(patched)
    if post['header'] != root_hdr: raise ValueError('FDT header changed unexpectedly')
    expected = set(nodes)-{p for p in nodes if p==LINK or p.startswith(LINK+'/')}
    if set(post['nodes']) != expected:
        raise ValueError('Unexpected node changes')
    expectprops = {key:val[4] for key,val in props.items() if key[0] in expected}
    expectprops[(EARC,'status')] = b'disabled\0'
    actualprops = {key:val[4] for key,val in post['props'].items()}
    if actualprops != expectprops:
        raise ValueError('Unexpected property changes')
    return patched, {'input_sha256':hexsha(data),'output_sha256':hexsha(patched),
                     'unchanged_header_and_file_size':len(data),
                     'removed_node':LINK, 'disabled_node':EARC,
                     'retained_nodes':len(post['nodes']),
                     'remaining_dai_links':sorted(k for k in post['nodes'] if k.startswith('/auge_sound/aml-audio-card,dai-link@') and k.count('/')==2),
                     'all_other_properties_unchanged':True,
                     'bootable': 'NOT VERIFIED; OFFLINE EXPERIMENT ONLY'}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input_dtb',type=Path)
    ap.add_argument('output_dtb',type=Path)
    a=ap.parse_args()
    if a.input_dtb.resolve()==a.output_dtb.resolve(): raise SystemExit('Input and output must differ')
    data=a.input_dtb.read_bytes()
    # Deliberately pin to a verified input to avoid patching an incompatible layout.
    want='5d3902b74ad206078503051c858be97963b7307f21d102c20a078c75e5a900fc'
    if hexsha(data)!=want: raise SystemExit('Input does not match the supplied LAKI V4 running DTB SHA-256. Refusing.')
    out,report=patch(data)
    a.output_dtb.write_bytes(out)
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
