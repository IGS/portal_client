
# Contains the functions to convert any of the three valid inputs into a 
# manifest data structure that process_manifest requires.
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 2.7 lib(s)
import urllib2
# additional dependencies (get from pip) 
import boto

# Takes in a local file which contains manifest data and converts it to the data
# stucture that is expected for the function download_manifest() in 
# process_manifest.py
def file_to_manifest(file):

# Takes in a URL where a manifest file is hosted and creates the same data
# stucture that is expected for the function download_manifest() in 
# process_manifest.py
def url_to_manifest(url):

# Takes in a token that correspondes to a cart/manifest entity. This is then
# converted into the data structure expected for the function download_manifest() 
# in process_manifest.py
def token_to_manifest(url):