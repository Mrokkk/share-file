#!/usr/bin/env python3

MAX_CONNECTIONS = 2
CHUNK_SIZE = 4096

class FileHeader:

    def __init__(self, size, crc=0):
        self.size = size
        self.crc = crc

