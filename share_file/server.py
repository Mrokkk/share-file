#!/usr/bin/env python3

import os
import pickle
import socket
import logging
import netifaces as ni
from base64 import b64encode

from .crc import *
from .definitions import *

logger = logging.getLogger(__name__)

def read_interfaces_ip():
    ip_addresses = []
    for interface in ni.interfaces():
        try:
            ip_addresses.append(ni.ifaddresses(interface)[ni.AF_INET][0]['addr'])
        except:
            pass
    if not len(ip_addresses):
        raise RuntimeError('No interfaces!')
    return ip_addresses

def read_from_file(conn, file):
    logger.debug('Sending file by %d B chunks...', CHUNK_SIZE)
    data = file.read(CHUNK_SIZE)
    while (data):
        conn.send(data)
        data = file.read(CHUNK_SIZE)
    logger.debug('Finished transfer')

def server_loop(sock, filename):
    while True:
        (conn, address) = sock.accept()
        logger.info('Got connection from %s', conn.getpeername())
        header = FileHeader(os.path.getsize(filename), crc32_file(filename))
        logger.debug('File size: %d B', header.size)
        logger.debug('File CRC32: 0x%x', header.crc)
        serialized_header = bytes(pickle.dumps(header))
        conn.send(serialized_header)
        logger.debug('Sent header')
        data = conn.recv(1024)
        if not data:
            logger.info('%s closed connection', conn.getpeername())
            conn.close()
            continue
        logger.debug('Received ACK')
        with open(filename, 'rb') as f:
            read_from_file(conn, f)
            logger.info('Closing connection with %s', conn.getpeername())
            conn.close()

def main(args):
    filename = args.file
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        os.stat(filename)
        sock.bind(('0.0.0.0', 0))
        address = sock.getsockname()
        ip_addresses = read_interfaces_ip()
        logger.debug('Filename: %s', filename)
        logger.debug('Running server on: %s', address)
        logger.debug('NetIfaces IPs: %s', ip_addresses)
        t = [ip_addresses, address[1]]
        serialized_tuple = bytes(os.path.basename(filename) + ':', 'utf-8') + b64encode(pickle.dumps(t))
        print(serialized_tuple.decode('utf-8'))
        sock.listen(MAX_CONNECTIONS)
        server_loop(sock, filename)
    except KeyboardInterrupt:
        print('')
    except OSError as exc:
        logger.error('OSError: %s', str(exc))
    except RuntimeError as exc:
        logger.error('RuntimeError: %s', str(exc))
    except Exception as exc:
        logger.error('Unexpected error: %s', str(exc))

def add_share_command(subparsers):
    parser_share = subparsers.add_parser('share')
    parser_share.add_argument('file')
    parser_share.set_defaults(func=main)
