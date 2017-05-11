#!/usr/bin/env python3

import os
import pickle
import socket
import logging
import argparse
import progressbar
import netifaces as ni
from base64 import b64encode, b64decode

MAX_CONNECTIONS = 2
CHUNK_SIZE = 4096

class FileHeader:

    def __init__(self, size, crc=0):
        self.size = size
        self.crc = crc

def get_ips():
    ip_addresses = []
    for interface in ni.interfaces():
        try:
            ip_addresses.append(ni.ifaddresses(interface)[ni.AF_INET][0]['addr'])
        except:
            pass
    return ip_addresses

def read_from_file(conn, file):
    data = file.read(CHUNK_SIZE)
    while (data):
        conn.send(data)
        data = file.read(CHUNK_SIZE)

def share(args):
    filename = args.file
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0))
    address = sock.getsockname()
    ip_addresses = get_ips()
    logging.debug('Running server on: %s', address)
    logging.debug('NetIfaces IPs: %s', ip_addresses)
    data_to_send = [ip_addresses, address[1]]
    serialized = bytes(os.path.basename(filename) + ':', 'utf-8') + b64encode(pickle.dumps(data_to_send))
    print(serialized.decode('utf-8'))
    sock.listen(MAX_CONNECTIONS)
    while True:
        try:
            (conn, address) = sock.accept()
            header = FileHeader(os.path.getsize(filename))
            serialized_header = bytes(pickle.dumps(header))
            conn.send(serialized_header)
            data = conn.recv(1024)
            if not data:
                conn.close()
                continue
            with open(filename, 'rb') as f:
                read_from_file(conn, f)
                conn.close()
        except KeyboardInterrupt:
            print('')
            return

def write_to_file(sock, file, filesize):
    with progressbar.DataTransferBar(min_value=0, max_value=filesize) as bar:
        read_size = 0
        data = sock.recv(CHUNK_SIZE)
        if filesize < CHUNK_SIZE:
            read_size = filesize
        while (data):
            file.write(data)
            bar.update(read_size)
            read_size += CHUNK_SIZE
            data = sock.recv(CHUNK_SIZE)

def ask_for_file(filename, size):
    answer = input('Do you want to accept ' + filename + ' with size ' + str(size) + 'B? [Y/n] ').lower()
    if answer == '' or answer == 'y':
        return False
    return True

def get_file(filename, ip_addresses, port, no_confirm=False):
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
        if not no_confirm:
            if ask_for_file(filename, header.size):
                return
        sock.send(b'OK')
        with open(filename, 'wb') as file:
            write_to_file(sock, file, header.size)
            return
    logging.error('Cannot connect to server')

def get(args):
    data = args.key
    filename = data.split(':')[0]
    serialized = b64decode(bytes(data.split(':')[1], 'ascii'))
    t = pickle.loads(serialized)
    logging.debug('Filename: %s', filename)
    logging.debug('Data: %s', t)
    ip_addresses = t[0]
    port = t[1]
    get_file(filename, ip_addresses, port, no_confirm=args.no_confirm)

def add_share_command(subparsers):
    parser_share = subparsers.add_parser('share')
    parser_share.add_argument('file')
    parser_share.set_defaults(func=share)

def add_get_command(subparsers):
    parser_share = subparsers.add_parser('get')
    parser_share.add_argument('-y', '--no-confirm', action='store_true')
    parser_share.add_argument('key')
    parser_share.set_defaults(func=get)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    subparsers = parser.add_subparsers(help='sub-command help')
    add_share_command(subparsers)
    add_get_command(subparsers)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    args.func(args)

def main():
    args = parse_args()

if __name__ == "__main__":
    main()
