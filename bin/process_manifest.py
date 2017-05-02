
# Contains the functions for downloading the contents of a manifest. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 2.7 lib(s)
import urllib2,hashlib
# additional dependencies (get from pip) 
import boto

# Accepts a manifest data structure which is a dict where the key is the unique
# ID of the file designated by OSDF. The value is then another dict which contains
# all URLs present as well as the MD5 for the file. 
def download_manifest(manifest):