#!/usr/bin/env python3

import os
import pickle
import socket
import logging
import progressbar
from base64 import b64decode

from .crc import *
from .definitions import *

logger = logging.getLogger(__name__)

def read_from_socket(sock, file, filesize):
    logger.debug('Receiving file...')
    with progressbar.DataTransferBar(min_value=0, max_value=filesize) as bar:
        read_size = 0
        data = sock.recv(CHUNK_SIZE)
        if not data:
            raise RuntimeError('No data from server')
        if filesize < CHUNK_SIZE:
            read_size = filesize
        while (data):
            file.write(data)
            bar.update(read_size)
            read_size += min(CHUNK_SIZE, filesize - read_size)
            data = sock.recv(CHUNK_SIZE)
    logger.debug('Finished transfer')

def ask_for_file(filename, size):
    try:
        answer = input('Do you want to accept ' + filename + ' with size ' + str(size) + ' B? [Y/n] ').lower()
        if answer == '' or answer == 'y':
            return False
        return True
    except KeyboardInterrupt:
        print('')
        return True

def get_header(sock):
    logger.debug('Receiving header')
    serialized_header = sock.recv(1024)
    if not serialized_header:
        raise RuntimeError('No data from server!')
    return pickle.loads(serialized_header)

def checksum_verify(filename, expected):
    checksum = crc32_file(filename)
    if not checksum:
        raise RuntimeError('File empty!')
    if checksum != expected:
        raise RuntimeError('Bad checksum: 0x%x', checksum)

def get_file(filename, ip_addresses, port, no_confirm=False, no_checksum=False):
    for ip in ip_addresses:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except Exception as exc:
            logger.debug('Cannot connect to %s: %s', ip, str(exc))
            continue
        try:
            header = get_header(sock)
            logger.debug('File size: %d B', header.size)
            logger.debug('File CRC32: 0x%x', header.crc)
            if not no_confirm:
                if ask_for_file(filename, header.size):
                    return
            logger.debug('Sending ACK')
            sock.send(b'ACK')
            with open(filename, 'wb') as file:
                read_from_socket(sock, file, header.size)
            if not no_checksum:
                checksum_verify(filename, header.crc)
        except OSError as exc:
            logger.error('OSError: %s', str(exc))
        except RuntimeError as exc:
            logger.error('RuntimeError: %s', str(exc))
        except Exception as exc:
            logger.error('Unexpected error: %s', str(exc))
        return
    logger.error('Cannot connect to server')

def main(args):
    key_splitted = args.key.split(':')
    filename = key_splitted[0]
    serialized_tuple = b64decode(bytes(key_splitted[1], 'ascii'))
    t = pickle.loads(serialized_tuple)
    ip_addresses, port = t[0], t[1]
    logger.debug('Filename: %s', filename)
    logger.debug('IP addresses: %s; port: %d', ip_addresses, port)
    get_file(filename, ip_addresses, port, args.no_confirm, args.no_checksum)
