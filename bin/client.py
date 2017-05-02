
# Client that functions to download data from the HMP DACC (http://hmpdacc.org/)
# when provided either a manifest file (locally stored or at a URL/FTP endpoint) 
# or using a token generated from the portal at portal.ihmpdcc.org. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 2.7 lib(s)
import argparse

from process_manifest import download_manifest
from convert_to_manifest import file_to_manifest,url_to_manifest,token_to_manifest

def main():

    parser = argparse.ArgumentParser(description='HMP client to download files given a manifest file generated from portal.ihmpdcc.org.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-manifest', type=str, help='Location of a locally stored manifest file from portal.ihmpdcc.org.')
    group.add_argument('-url', type=str, required=False, help='URL path to a manifest file stored at a HTTP/FTP endpoint.')
    group.add_argument('-token', type=str, required=False, help='Token string generated for a cart from portal.ihmpdcc.org.')
    parser.add_argument('-destination', type=str, required=False, default=".", help='Location to place all the downloads.')
    args = parser.parse_args()

    if args.manifest:
        download_manifest(file_to_manifest(args.manifest),args.destination)

    elif args.url: 
        download_manifest(url_to_manifest(args.url),args.destination)

    elif args.token:
        download_manifest(token_to_manifest(args.token),args.destination)

if __name__ == '__main__':
    main()