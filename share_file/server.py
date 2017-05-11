#!/usr/bin/env python3

import os
import pickle
import socket
import logging
import netifaces as ni
from base64 import b64encode
from .definitions import *

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

def server_loop(sock, filename):
    while True:
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
    try:
        server_loop(sock, filename)
    except KeyboardInterrupt:
        print('')
