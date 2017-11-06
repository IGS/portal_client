#!/usr/bin/env python3

# Convert HMP Portal manifest file to a shell script containing ascp download commands.
#
# Usage: manifest2ascp.py -manifest=hmp_cart_t2d_june_12_2017.tsv -user=username -password=password -ascp_options-"-l 200M" > download-file.sh
#
# HMP Portal: http://portal.ihmpdcc.org
# ascp (Aspera FASP client): http://downloads.asperasoft.com/en/downloads/2
#
# Author: Jonathan Crabtree
# Contact: jcrabtree@som.umaryland.edu

import argparse
import csv
import re
import sys

# Default values
DFLT_ASCP_PATH = "~/.aspera/connect/bin/ascp"
DFLT_ASCP_OPTIONS = ""

def format_time(s):
    hours = s / 3600.0
    ttime = "{0:.2f}".format(hours) + " hours"
    if hours > 36:
        days = hours / 24.0
        ttime = "{0:.2f}".format(days) + " days"
    return ttime

def main():
    # command line arguments
    parser = argparse.ArgumentParser(description='Convert HMP Portal manifest file to a shell script containing ascp download commands.')
    parser.add_argument('-m', '--manifest', type=str, required=True, help='Location of a locally stored manifest file from portal.ihmpdcc.org.')
    parser.add_argument('-a', '--ascp_path', type=str, required=False, default=DFLT_ASCP_PATH, help='Path to Aspera ascp executable.')
    parser.add_argument('-o', '--ascp_options', type=str, required=False, default=DFLT_ASCP_OPTIONS, help='Additional options to pass to ascp.')
    parser.add_argument('-u', '--user', type=str, required=True, help='IGS-supplied Aspera username.')
    parser.add_argument('-p', '--password', type=str, required=True, help='IGS-supplied Aspera password.')
    args = parser.parse_args()
    
    print("#!/bin/bash")
    print("export ASCP=" + args.ascp_path)
    print("export ASPERA_USER=" + args.user)
    print("export ASPERA_SCP_PASS=" + args.password)
    print("")

    # count fasp and non-fasp URLs
    num_fasp = 0
    num_not_fasp = 0
    num_private = 0
    num_no_size = 0
    total_bytes = 0
    lnum = 0

    # read manifest file
    with open(args.manifest, 'r') as file:
        r = csv.reader(file, delimiter="\t")
        for line in r:
            lnum += 1
            md5 = line[1]
            size = line[2]
            url = line[3]

            # Aspera fasp URL
            m = re.search('fasp://([^/]+)/(.*)$', url)
            if m:
                host = m.group(1)
                path = m.group(2)
                # print corresponding ascp command to output script
                # "-d" - create target directory/directories
                command = args.ascp_path + " -d "
                if args.ascp_options != "":
                    command = command + " " + args.ascp_options
                command = command + " " + args.user + "@" + host + ":" + path + " ./" + path
                print(command)
                num_fasp += 1

                # file with no size specified
                if size == "":
                    sys.stderr.write("WARN - file " + url + " has no size\n")
                    num_no_size += 1
                else:
                    total_bytes += int(size)
                continue
                
            # non-fasp URL
            m = re.search('(http|ftp)', url)
            if m:
                num_not_fasp += 1
                continue

            # private node (i.e., data for this file were not uploaded to the DCC)
            m = re.search('^private', url)
            if m:
                num_private +=1
                continue
    
            # anything else
            if lnum != 1:
                sys.stderr.write("ERROR - unrecognized URL in manifest file at line " + str(lnum) + ": " + url)

        # print summary
        sys.stderr.write("INFO - read " + str(lnum) + " line(s) from " + args.manifest + "\n")
        sys.stderr.write("INFO - skipped " + str(num_not_fasp) + " non-fasp URLs\n")
        sys.stderr.write("INFO - skipped " + str(num_private) + " private files with no data available from the DCC\n")
        sys.stderr.write("INFO - wrote " + str(num_fasp) + " fasp URLs to output\n")
        sys.stderr.write("INFO - found " + str(num_no_size) + " files with no file size specified\n")

        gb = total_bytes / pow(2.0,30.0)
        total_msg = "INFO - total gigabytes to transfer = " + str(gb)
        if num_no_size > 0:
            total_msg = total_msg + ", **excluding files with no size**"
        sys.stderr.write(total_msg + "\n")

        # 10MBps is approximately 1.25 Mb/second
        t10secs = (gb / (1.25/1024.0))
        t10_ttime = format_time(t10secs)

        t200secs = (gb / (1.25/1024.0)) / 20.0
        t200_ttime = format_time(t200secs)

        if num_no_size > 0:
            t10_ttime = t10_ttime + ", **excluding files with no size**"
            t200_ttime = t200_ttime + ", **excluding files with no size**"

        sys.stderr.write("INFO - _approximate_ total transfer time at 10Mbps = " + t10_ttime + "\n")
        sys.stderr.write("INFO - _approximate_ total transfer time at 200Mbps = " + t200_ttime + "\n")

if __name__ == '__main__':
    main()
