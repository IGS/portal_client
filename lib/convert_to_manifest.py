"""
Contains the functions to convert any of the three valid inputs into a
manifest data structure that the manifest processor requires.
"""

import urllib
import csv
import io
import logging
import sys

logger = logging.getLogger(__name__)

def file_to_manifest(file):
    """
    Takes in a local file which contains manifest data and converts it to the
    data stucture that is expected for the function download_manifest() in
    process_manifest.py
    """
    logger.debug("In file_to_manifest.")

    with open(file) as tsv:
        return tsv_to_manifest(tsv)

def url_to_manifest(url):
    """
    Takes in a URL where a TSV manifest file is hosted and creates the same data
    stucture that is expected for the function download_manifest() in
    process_manifest.py
    """
    logger.debug("In url_to_manifest.")

    response = urllib.request.urlopen(url)

    return tsv_to_manifest(io.TextIOWrapper(response))

def tsv_to_manifest(tsv_object):
    """
    Function that takes in either a file or a URL response from a TSV entity and
    converts it into the manifest data structure expected for
    download_manifest().
    """
    logger.debug("In tsv_to_manifest.")

    manifest = []
    ids = {}

    reader = csv.reader(tsv_object, delimiter="\t")
    next(reader, None) # skip the manifest header

    for row in reader:
        if row[0] not in ids:
            manifest.append({
                'id':row[0],
                'md5':row[1],
                'urls':row[3]
            })
            ids[row[0]] = 1

    return manifest
