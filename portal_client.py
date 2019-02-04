#!/usr/bin/env python3

# The portal client downloads data from the portal instance when provided with
# a manifest file (locally stored or at a URL/FTP endpoint)

import argparse
import getpass
import logging
import os
import errno
import sys

from manifest_processor import ManifestProcessor
from convert_to_manifest import file_to_manifest
from convert_to_manifest import url_to_manifest
from convert_to_manifest import token_to_manifest

def set_logging():
    """ Setup logging. """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

def parse_cli():
    parser = argparse.ArgumentParser(
        description='Client to download files given a manifest file ' +
                    'generated from a portal instance.'
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '-m', '--manifest',
        type=str,
        help='Location of a locally stored manifest file from.'
    )

    group.add_argument(
        '-u', '--url',
        type=str,
        required=False,
        help='URL path to a manifest file stored at an HTTP endpoint.'
    )

    group.add_argument(
        '-t', '--token',
        type=str,
        required=False,
        help='Token string generated for a cart from portal.ihmpdcc.org.'
    )

    parser.add_argument(
        '--client-secrets',
        type=str,
        required=False,
        default="",
        help='The path to a client secrets JSON file obtain from Google. ' + \
             'When using GCP (Google Cloud Platform) storage endpoints (' + \
             'urls that begin with "gs://"), this option is required.'
    )

    parser.add_argument(
        '-d', '--destination',
        type=str,
        required=False,
        default=".",
        help='Optional location to place all the downloads. ' + \
             'Defaults to the current directory.'
    )

    parser.add_argument(
        '--endpoint-priority',
        type=str,
        required=False,
        default="",
        help='Optional comma-separated protocol priorities (descending). ' + \
             'The valid protocols are "HTTP", "FTP", "FASP", "S3" and "GS" ' + \
             '(and defaults to that order).'
    )

    parser.add_argument(
        '--user',
        type=str,
        required=False,
        help='The username to authenticate with when using Aspera ' + \
             'endpoints. All FASP (aspera) endpoints require ' + \
             'authentication. Note: Using --user will automatically ' + \
             'trigger an interactive request for a password.'
    )

    parser.add_argument(
        '-r', '--retries',
        type=int,
        required=False,
        default=0,
        help='Optional number of retries to perform in case of download ' + \
             'failures. Defaults to 0.'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Display additional debugging information/logs at runtime.'
    )

    args = parser.parse_args()

    return args

def validate_cli():
    if 'FASP'in endpoints and args.user == None:
        sys.stderr.write("Must specify username with --user when " + \
                         "retrieving data with aspera/fasp.\n")
        sys.exit(1)

    if 'GS' in endpoints and args.client_secrets == None:
        sys.stderr.write("Must specify --client-secrets files when " + \
                         "retrieving google storage data.\n")
        sys.exit(1)

def main():
    args = parse_cli()

    if args.debug:
        set_logging()

    default_endpoint_priority = ['HTTP', 'FTP', 'S3']
    valid_endpoints = ['HTTP', 'FTP', 'S3', 'FASP', 'GS']

    if args.endpoint_priority != "":
        endpoints = args.endpoint_priority.split(',')

        for endpoint in endpoints:
            if endpoint not in valid_endpoints:
                sys.stderr.write("Error: Invalid protocol. Please check " + \
                    "the endpoint-priority option for valid entries.\n");
                sys.exit(1)
    else:
        endpoints = default_endpoint_priority

    if args.destination != ".":
        try:
            os.makedirs(args.destination)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    validate_cli()

    username = args.user
    destination = args.destination
    password = None

    if 'FASP' in endpoints and len(args.user) > 0:
        # Ask for the password
        password = getpass.getpass(
            "Enter your password (Don't worry, it's not shown): "
        )

    keep_trying = True
    attempts = 0
    result = []

    mp = ManifestProcessor(username, password)

    while keep_trying:
        manifest = {}

        if args.manifest:
            manifest = file_to_manifest(args.manifest)
        elif args.url:
            manifest = url_to_manifest(args.url)
        elif args.token:
            manifest = token_to_manifest(args.token)


        result = mp.download_manifest(
            manifest,
            destination,
            args.endpoint_priority
        )

        if len(result) == 0 or result.count(0) == len(result):
            # No failures found
            keep_trying = False
        else:
            retry_results_msg(
                len(result),
                result.count(1),
                result.count(2),
                result.count(3)
            )

            if attempts == args.retries:
                keep_trying = False
            else:
                attempts += 1
                print("Initiating download attempt number {}...\n".format(attempts))

                # Never going to get anywhere if no URLs are present
                if result.count(1) == len(result):
                    keep_trying = False

# Outputs the results of those files that failed to download
def retry_results_msg(file_count, failure_1, failure_2, failure_3):

    msg = "\nNot all files in manifest (total of {0}) were downloaded successfully. Number of failures:\n" \
        "{1} -- no valid URL in the manifest file\n" \
        "{2} -- URL present in manifest, but not accessible at the location specified\n" \
        "{3} -- MD5 checksum failed for file (file is corrupted or the wrong MD5 is attached to the file"

    print(msg.format(file_count,failure_1,failure_2,failure_3))

if __name__ == '__main__':
    main()
