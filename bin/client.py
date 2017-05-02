
#
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 2.7 lib(s)
import argparse

import process_manifest
import convert_to_manifest

def main():

    parser = argparse.ArgumentParser(description='HMP client to download files given a manifest file generated from portal.ihmpdcc.org.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-manifest', type=str, help='Location of a locally stored manifest file from portal.ihmpdcc.org.')
    group.add_argument('-url', type=str, required=False, help='URL path to a manifest file stored at a HTTP/FTP endpoint.')
    group.add_argument('-token', type=str, required=False, help='Token string generated for a cart from portal.ihmpdcc.org.')
    args = parser.parse_args()

    if args.manifest:
        print(args.manifest)

    elif args.url: # a URL is just one step from being the same as manifest
        print(args.url)

    elif args.token:
        print(args.token)

if __name__ == '__main__':
    main()