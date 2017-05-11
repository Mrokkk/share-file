#!/usr/bin/env python3

import logging
import argparse
from share_file import server, client

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    subparsers = parser.add_subparsers(help='sub-command help')
    server.add_share_command(subparsers)
    client.add_get_command(subparsers)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    args.func(args)

if __name__ == "__main__":
    main()
