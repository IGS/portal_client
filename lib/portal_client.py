#!/usr/bin/env python3

# The portal client downloads data from a portal instance when provided with
# a manifest file (locally stored or at an HTTP endpoint)

import argparse
import logging
import os
import errno
import sys

from manifest_processor import ManifestProcessor
from convert_to_manifest import file_to_manifest
from convert_to_manifest import url_to_manifest
from convert_to_manifest import token_to_manifest

logger = logging.getLogger()

def obtain_password():
    """
    Interactively obtain the user's password (securely).
    """
    logger.debug("In obtain_password.")
    import getpass

    print("Enter your password: (masked)")
    password = getpass.getpass('')

    return password

def set_logging():
    """
    Setup logging.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    root.addHandler(ch)

def get_version():
    """
    Determine the version of the installed portal_client.
    """
    import pkg_resources

    version = None

    try:
        version = pkg_resources.get_distribution('portal_client').version
    except Exception:
        logger.warning("Unable to determine version.")
        version = "?"

    return version

def parse_cli():
    """
    Establishes the CLI interface by defining the parameter names and
    what types of data they accept. Creates the command line parser
    and parses the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Client to download data described by a manifest file ' + \
                    'generated from a portal instance.'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + get_version()
    )

    parser.add_argument(
        '-m', '--manifest',
        type=str,
        help='Location of a locally stored manifest file.'
    )

    parser.add_argument(
        '-u', '--url',
        type=str,
        required=False,
        help='URL path to a manifest file stored at an HTTP endpoint.'
    )

    parser.add_argument(
        '--disable-validation',
        dest='disable_validation',
        action='store_true',
        help='Disable MD5 checksum validation.'
    )

    parser.add_argument(
        '-t', '--token',
        type=str,
        required=False,
        help='Token string generated for a cart from portal.ihmpdcc.org.'
    )

    parser.add_argument(
        '--google-client-secrets',
        type=str,
        required=False,
        dest='client_secrets',
        help='The path to a client secrets JSON file obtain from Google. ' + \
             'When using GCP (Google Cloud Platform) storage endpoints (' + \
             'urls that begin with "gs://"), this option is required.'
    )

    parser.add_argument(
        '--google-project-id',
        type=str,
        required=False,
        dest='project_id',
        help='The Google project ID to use. When using GCP (Google ' + \
              'Cloud Platform) storage endpoints, this option is required.'
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

    # This is later populated if the user specifies the --user argument.
    args.password = None

    return args

def validate_cli(args, endpoints):
    """
    Determine if the user has invoked the tool properly based on what
    endpoints, if any, were specified. Different endpoints have different
    requirements (for authentication), so invocations can vary.
    """
    logger.debug("In validate_cli.")
    cli_error = False

    if 'FASP' in endpoints:
        import aspera
        if not aspera.is_ascp_installed():
            sys.stderr.write("The ASCP binary is not installed or available.\n")
            sys.stderr.write("Please install it or adjust yor PATH.\n")
            cli_error = True

        if args.user is None:
            sys.stderr.write("Must specify username with --user when " + \
                             "retrieving data with aspera/fasp.\n")
            cli_error = True

    if 'GS' in endpoints and (args.client_secrets is None or args.project_id is None):
        sys.stderr.write("Must specify both --google-client-secrets and " + \
                         "--google-project-id when retrieving data from Google.\n")
        cli_error = True

    if args.user is not None:
        password = obtain_password()
        args.password = password

    if cli_error:
        logger.error("Aborting execution.")
        sys.exit(1)

def retry_results_msg(file_count, failure_1, failure_2, failure_3):
    """
    Outputs the results of those files that failed to download.
    """

    msg = "Not all files (total of {0}) were downloaded successfully. Number of failures:\n" \
        "{1} -- no valid URL in the manifest file\n" \
        "{2} -- URL is present in manifest, but not accessible at the location specified\n" \
        "{3} -- MD5 checksum failed for file (file is corrupted or the wrong MD5 is associated)"

    print()
    print(msg.format(file_count, failure_1, failure_2, failure_3))

def main():
    """
    The entrypoint into the portal_client code.
    """
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
                    "the endpoint-priority option for valid entries.\n")
                sys.exit(1)
    else:
        endpoints = default_endpoint_priority

    if args.destination != ".":
        try:
            os.makedirs(args.destination)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    validate_cli(args, endpoints)

    username = args.user
    destination = args.destination
    password = args.password

    # GCP Information
    client_secrets = args.client_secrets
    project_id = args.project_id

    keep_trying = True
    attempts = 0
    result = []

    logger.debug("Creating ManifestProcessor.")
    mp = ManifestProcessor(username, password,
                           google_client_secrets=client_secrets,
                           google_project_id=project_id)

    # Turn off MD5 checksumming if specified by the user
    if args.disable_validation:
        logger.debug("Turning off checksum validation.")
        mp.disable_validation()

    while keep_trying:
        manifest = {}

        if args.manifest:
            manifest = file_to_manifest(args.manifest)
        elif args.url:
            manifest = url_to_manifest(args.url)
        elif args.token:
            manifest = token_to_manifest(args.token)

        logger.debug("About to start downloading manifest.")

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

if __name__ == '__main__':
    main()
