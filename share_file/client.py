#!/usr/bin/env python3

import os
import pickle
import socket
import logging
import progressbar
from base64 import b64decode

from .crc import *
from .definitions import *

def read_from_socket(sock, file, filesize):
    with progressbar.DataTransferBar(min_value=0, max_value=filesize) as bar:
        read_size = 0
        data = sock.recv(CHUNK_SIZE)
        if filesize < CHUNK_SIZE:
            read_size = filesize
        while (data):
            file.write(data)
            bar.update(read_size)
            read_size += min(CHUNK_SIZE, filesize - read_size)
            data = sock.recv(CHUNK_SIZE)

def ask_for_file(filename, size):
    answer = input('Do you want to accept ' + filename + ' with size ' + str(size) + ' B? [Y/n] ').lower()
    if answer == '' or answer == 'y':
        return False
    return True

def get_file(filename, ip_addresses, port, no_confirm=False, no_checksum=False):
    for ip in ip_addresses:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except Exception as exc:
            logging.debug('Cannot connect to %s: %s', ip, str(exc))
            continue
        serialized_header = sock.recv(1024)
        header = pickle.loads(serialized_header)
        logging.debug('File size: %d B', header.size)
        logging.debug('File CRC32: 0x%x', header.crc)
        if not no_confirm:
            if ask_for_file(filename, header.size):
                return
        sock.send(b'ACK')
        with open(filename, 'wb') as file:
            read_from_socket(sock, file, header.size)
        if not no_checksum:
            checksum = crc32_file(filename)
            if checksum != header.crc:
                logging.error('Bad checksum: 0x%x', checksum)
        return
    logging.error('Cannot connect to server')

def main(args):
    key_splitted = args.key.split(':')
    filename = key_splitted[0]
    serialized_tuple = b64decode(bytes(key_splitted[1], 'ascii'))
    t = pickle.loads(serialized_tuple)
    logging.debug('Filename: %s', filename)
    logging.debug('Data: %s', t)
    ip_addresses = t[0]
    port = t[1]
    get_file(filename, ip_addresses, port, args.no_confirm, args.no_checksum)
