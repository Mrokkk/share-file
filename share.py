#!/usr/bin/env python3

import logging
import argparse
from share_file import server, client

def add_share_command(subparsers):
    parser_share = subparsers.add_parser('share')
    parser_share.add_argument('file')
    parser_share.set_defaults(func=server.main)

def add_get_command(subparsers):
    parser_share = subparsers.add_parser('get')
    parser_share.add_argument('-y', '--no-confirm', action='store_true')
    parser_share.add_argument('key')
    parser_share.set_defaults(func=client.main)

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
