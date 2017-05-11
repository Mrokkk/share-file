#!/usr/bin/env python3

from zlib import crc32

def crc32_file(filename):
    current = 0
    with open(filename, 'rb') as f:
        while True:
            buffer = f.read(8192)
            if not buffer:
                break
            current = crc32(buffer, current)
            return current

