#!/usr/bin/env python3

# Client that functions to download data from the HMP DACC (http://hmpdacc.org/)
# when provided either a manifest file (locally stored or at a URL/FTP endpoint) 
# or using a token generated from the portal at portal.ihmpdcc.org. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 3.6 lib(s)
import argparse,os,errno,sys

from process_manifest import download_manifest
from convert_to_manifest import file_to_manifest,url_to_manifest,token_to_manifest

def main():

    parser = argparse.ArgumentParser(description='HMP client to download files given a manifest file generated from portal.ihmpdcc.org.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-m', '--manifest', type=str, help='Location of a locally stored manifest file from portal.ihmpdcc.org.')
    group.add_argument('-u', '--url', type=str, required=False, help='URL path to a manifest file stored at a HTTP/FTP endpoint.')
    group.add_argument('-t', '--token', type=str, required=False, help='Token string generated for a cart from portal.ihmpdcc.org.')
    parser.add_argument('-d', '--destination', type=str, required=False, default=".", help='Optional location to place all the downloads. Defaults to the current directory.')
    parser.add_argument('-p', '--endpoint_priority', type=str, required=False, default="", help='Optional comma-separated endpoint priorities (in order of highest to lowest). The only valid endpoints for this client are "HTTP","FTP", and "S3" (and defaults to that order).')
    parser.add_argument('-b', '--block_size', type=int, required=False, default=123456, help='Optional size of bytes to return iteratively. Increasing requires fewer individual calls for the FTP/S3 endpoints and can speed up the download. Defaults to 123456.')
    parser.add_argument('-r', '--retries', type=int, required=False, default=0, help='Optional number of retries to perform in case of download failures. Defaults to 0.')

    # allow single-dash for any pre-1.3 long option for reverse-compatibility
    # (but don't show them in the help message)
    pre13_opts = { '-manifest': 1, '-url': 1, '-token': 1, '-destination': 1, '-endpoint_priority': 1, '-block_size': 1, '-retries': 1 }
    new_argv = []
    for arg in sys.argv:
        if arg in pre13_opts:
            arg = '-' + arg
        new_argv.append(arg)
    sys.argv = new_argv

    args = parser.parse_args()

    if args.endpoint_priority != "":
        eps = args.endpoint_priority.split(',')
        for ep in eps:
            if ep not in ['HTTP','FTP','S3']:
                sys.exit("Error -- Entered a non-valid endpoint. Please check the endpoint_priority option for what are considered valid entries.")

    if args.destination != ".":
        try:
            os.makedirs(args.destination)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    keep_trying = True
    attempts = 0
    result = []

    while keep_trying:

        manifest = {}

        if args.manifest:
            manifest = file_to_manifest(args.manifest)
            
        elif args.url: 
            manifest = url_to_manifest(args.url)

        elif args.token:
            manifest = token_to_manifest(args.token)

        result = download_manifest(manifest,args.destination,args.endpoint_priority,args.block_size)

        if len(result) == 0 or result.count(0) == len(result): # no failures found
            keep_trying = False

        else: 
            retry_results_msg(len(result),result.count(1),result.count(2),result.count(3))

            if attempts == args.retries:
                keep_trying = False
            else:
                attempts += 1
                print("\nDownload retry attempt number {0} initiating...\n".format(attempts))

                if result.count(1) == len(result): # never going to get anywhere if no URLs are present
                    keep_trying = False

# Outputs the results of those files that failed to download
def retry_results_msg(file_count,failure_1,failure_2,failure_3):

    msg = "\nNot all files in manifest (total of {0}) were downloaded successfully. Number of failures:\n" \
        "{1} -- no valid URL in the manifest file\n" \
        "{2} -- URL present in manifest, but not accessible at the location specified\n" \
        "{3} -- MD5 check failed for file (file is corrupted or the wrong MD5 is attached to the file" 

    print(msg.format(file_count,failure_1,failure_2,failure_3))

if __name__ == '__main__':
    main()
