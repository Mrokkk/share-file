#!/usr/bin/env python3

import os
import pickle
import socket
import asyncio
import argparse
import netifaces as ni
from numpy import uint8
from base64 import b64encode, b64decode

def get_ips():
    ip_addresses = []
    for interface in ni.interfaces():
        try:
            ip_addresses.append(ni.ifaddresses(interface)[ni.AF_INET][0]['addr'])
        except:
            pass
    return ip_addresses

def spawn_server(filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 8080))
    address = sock.getsockname()
    ip_addresses = get_ips()
    print('Running server on :', address)
    print('NetIfaces IPs :', ip_addresses)
    data_to_send = [ip_addresses, address[1]]
    serialized = bytes(filename + ':', 'utf-8') + b64encode(pickle.dumps(data_to_send))
    print(serialized.decode('utf-8'))
    sock.listen(2)
    while True:
        try:
            (conn, address) = sock.accept()
            with open(filename, 'rb') as f:
                conn.send(f.read())
                conn.close()
        except KeyboardInterrupt:
            print('')
            return

def share(args):
    spawn_server(args.file)

def write_to_file(sock, file):
    data = sock.recv(1024)
    while (data):
        file.write(data)
        data = sock.recv(1024)

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
    print('Called get on', data)
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