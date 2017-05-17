
# Client that functions to download data from the HMP DACC (http://hmpdacc.org/)
# when provided either a manifest file (locally stored or at a URL/FTP endpoint) 
# or using a token generated from the portal at portal.ihmpdcc.org. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 3.6 lib(s)
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
    parser.add_argument('-endpoint_priority', type=str, required=False, default="", help='Comma-separated endpoint priorities (in order of highest to lowest). The only valid endpoints for this client are "HTTP","FTP", and "S3".')
    args = parser.parse_args()

    if args.endpoint_priority != "":
        eps = args.endpoint_priority.split(',')
        for ep in eps:
            if ep not in ['HTTP','FTP','S3']:
                sys.exit("Error -- Entered a non-valid endpoint. Please check the endpoint_priority option for what are considered valid entries.")

    if args.manifest:
        download_manifest(file_to_manifest(args.manifest),args.destination,args.endpoint_priority)

    elif args.url: 
        download_manifest(url_to_manifest(args.url),args.destination,args.endpoint_priority)

    elif args.token:
        download_manifest(token_to_manifest(args.token),args.destination,args.endpoint_priority)

if __name__ == '__main__':
    main()