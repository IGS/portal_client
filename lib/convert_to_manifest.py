"""
Contains the functions to convert any of the three valid inputs into a
manifest data structure that the manifest processor requires.
"""

import urllib
import csv
import io
import logging
import sys

# Increase csv field size limit (useful when file is linked to many samples)
csv.field_size_limit(sys.maxsize)

# Initialize logger
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
    header = next(reader, None)
    if header is None:
        return manifest
    col = {name: i for i, name in enumerate(header)}
    required = {'file_id', 'md5', 'size', 'urls'}
    missing = required - col.keys()
    if missing:
        raise ValueError(f"Manifest is missing required columns: {missing}")

    for row in reader:
        file_id = row[col['file_id']]
        if file_id not in ids:
            manifest.append({
                'id': file_id,
                'md5': row[col['md5']],
                'size': int(row[col['size']]),
                'urls': row[col['urls']]
            })
            ids[file_id] = 1

    return manifest
