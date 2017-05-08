
# Contains the functions to convert any of the three valid inputs into a 
# manifest data structure that process_manifest requires.
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 3.6 lib(s)
import urllib,csv,io

# Takes in a local file which contains manifest data and converts it to the data
# stucture that is expected for the function download_manifest() in 
# process_manifest.py
def file_to_manifest(file):

    with open(file) as tsv:

        return tsv_to_manifest(tsv)

# Takes in a URL where a TSV manifest file is hosted and creates the same data
# stucture that is expected for the function download_manifest() in 
# process_manifest.py
def url_to_manifest(url):

    response = urllib.request.urlopen(url)

    return tsv_to_manifest(io.TextIOWrapper(response))

# Takes in a token that correspondes to a cart/manifest entity. This is then
# converted into the data structure expected for the function download_manifest() 
# in process_manifest.py
def token_to_manifest(token):
    return token

# Function that takes in either a file or a URL response from a TSV entity and
# converts it into the manifest data structure expected for download_manifest().
def tsv_to_manifest(tsv_object):

    manifest = {}

    reader = csv.reader(tsv_object,delimiter="\t")
    next(reader,None) # skip the manifest header

    for row in reader:
        manifest[row[0]] = {'md5':row[1],'urls':row[3],'id':row[0]}
    
    return manifest