#!/usr/bin/env python3
"""Strict donor Android 9 properties -> LAKI Hybrid V6; no other fields altered."""
from __future__ import annotations
import argparse
from pathlib import Path

EXPECTED = {
    'ro.product.model': 'N5MAX',
    'ro.product.brand': 'Amlogic',
    'ro.build.display.id': 'MGCTV152F20210607',
}
CHANGES = {
    'ro.product.model': 'm6cw4k',
    'ro.product.brand': 'LAKI',
    'ro.build.display.id': 'LAKI Hybrid V6 FULL AUDIO by DarkoBG',
}


def patch(data: bytes) -> bytes:
    if b'\x00' in data:
        raise ValueError('build.prop contains NUL bytes')
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('build.prop is not UTF-8') from exc
    if '\r\n' in text and '\n' in text.replace('\r\n', ''):
        raise ValueError('Mixed newline types; refusing')
    newline = '\r\n' if '\r\n' in text else '\n'
    original_terminal_newline = text.endswith(newline)
    result = []
    hits = {k: 0 for k in CHANGES}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in line:
            result.append(line)
            continue
        key, old = line.split('=', 1)
        key = key.strip()
        if key in CHANGES:
            hits[key] += 1
            if old.strip() != EXPECTED[key]:
                raise ValueError(f'Unexpected {key}={old.strip()!r}; expected {EXPECTED[key]!r}; aborting')
            line = key + '=' + CHANGES[key]
        result.append(line)
    invalid = {k: v for k, v in hits.items() if v != 1}
    if invalid:
        raise ValueError(f'Expected exactly one occurrence of each property; got {invalid}')
    out = newline.join(result) + (newline if original_terminal_newline else '')
    if out == text:
        raise ValueError('Nothing changed')
    for key, new in CHANGES.items():
        if out.count('\n' + key + '=') + int(out.startswith(key + '=')) != 1:
            raise ValueError(f'Post-check found duplicate {key}')
        if f'{key}={new}' not in out:
            raise ValueError(f'Missing new value {key}')
    return out.encode('utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('target', type=Path)
    args = ap.parse_args()
    if args.target.exists():
        raise SystemExit(f'Refusing to overwrite {args.target}')
    data = args.source.read_bytes()
    new = patch(data)
    args.target.write_bytes(new)
    print('OK: only ro.product.model, ro.product.brand, ro.build.display.id changed')
    for k, v in CHANGES.items():
        print(f'  {k}={v}')


if __name__ == '__main__':
    main()
