#!/usr/bin/env python3

import os
import pickle
import socket
import argparse
import netifaces as ni
from base64 import b64encode, b64decode

MAX_CONNECTIONS = 2
CHUNK_SIZE = 4096

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
    sock.bind(('0.0.0.0', 8080))
    address = sock.getsockname()
    ip_addresses = get_ips()
    print('Running server on :', address)
    print('NetIfaces IPs :', ip_addresses)
    data_to_send = [ip_addresses, address[1]]
    serialized = bytes(os.path.basename(filename) + ':', 'utf-8') + b64encode(pickle.dumps(data_to_send))
    print(serialized.decode('utf-8'))
    sock.listen(MAX_CONNECTIONS)
    while True:
        try:
            (conn, address) = sock.accept()
            with open(filename, 'rb') as f:
                read_from_file(conn, f)
                conn.close()
        except KeyboardInterrupt:
            print('')
            return

def write_to_file(sock, file):
    data = sock.recv(CHUNK_SIZE)
    while (data):
        file.write(data)
        data = sock.recv(CHUNK_SIZE)

def get_file(filename, ip_addresses, port):
    for ip in ip_addresses:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except:
            continue
        with open(filename, 'wb') as file:
            write_to_file(sock, file)

def get(args):
    data = args.key
    filename = data.split(':')[0]
    serialized = b64decode(bytes(data.split(':')[1], 'ascii'))
    t = pickle.loads(serialized)
    print('Filename:', filename)
    print('Data:', t)
    ip_addresses = t[0]
    port = t[1]
    get_file(filename, ip_addresses, port)

def add_share_command(subparsers):
    parser_share = subparsers.add_parser('share')
    parser_share.add_argument('file')
    parser_share.set_defaults(func=share)

def add_get_command(subparsers):
    parser_share = subparsers.add_parser('get')
    parser_share.add_argument('key')
    parser_share.set_defaults(func=get)

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')
    add_share_command(subparsers)
    add_get_command(subparsers)
    args = parser.parse_args()
    args.func(args)

def main():
    args = parse_args()

if __name__ == "__main__":
    main()
