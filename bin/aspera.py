#!/usr/bin/python

""" Wrapper module for ascp usage. """

import os
import re
import subprocess
import logging
import sys

# download example command(s):
#
# only getting ~ 10Mb/s (on 20-30Mb connection): with defaults:
#   ascp -T -v -L . testuser@aspera.ihmpdcc.org:test2.fsa ./
#   ascp -T -v -L . testuser@aspera.ihmpdcc.org:50MB ./
# closer to 20Mb/s with this option:
#   ascp -T -v -l 200M -L . testuser@aspera.ihmpdcc.org:50MB ./
#
# upload example command(s):
#   ascp -T -v -L . testuser@aspera.ihmpdcc.org:

# Create a module logger named after the module
logger = logging.getLogger(__name__)

# Add a NullHandler for the case if no logging is configured by the application
logger.addHandler(logging.NullHandler())

ASCP_COMMAND = "ascp"
ASCP_MIN_VERSION = '3.5'

# compare version numbers
def version_cmp(v1, v2):
    """
    Compare version/release numbers.
    """
    logger.debug("In version_cmp.")
    def normalize(v):
        """ Normalize a dotted version string. """
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]

    if sys.version_info[0] == 2:
        return cmp(normalize(v1), normalize(v2))
    else:
        nv1 = normalize(v1)
        nv2 = normalize(v2)
        result = (nv1 > nv2) - (nv1 < nv2)

        return result

def get_ascp_version():
    """
    Return version number of ascp executable referenced by ascp_command.
    May raise an exception if the path is invalid.
    """
    logger.debug("In get_ascp_version.")

    version = None
    output = subprocess.check_output([ASCP_COMMAND, "--version"],
                                     universal_newlines=True)

    cre = re.compile(r"^.+version (\d[\d\.]+)", re.MULTILINE)
    for match in cre.finditer(output):
        version = match.groups()[0]

    if version is None:
        raise Exception("Output from ascp command ('" + ASCP_COMMAND + \
                        " --version') did not contain a recognizable " + \
                        "version number.")
    return version

def check_ascp_version():
    """
    Check that the ascp utility is installed and that its version
    is within an acceptable range. If the utility is not present,
    or the version is unacceptable, an exception is raised.
    """
    logger.debug("In check_ascp_version.")

    # check ascp version, raise error if too low
    try:
        ascp_ver = get_ascp_version()
    except:
        raise Exception("Unable to determine ascp version. Is it installed?")

    if version_cmp(ascp_ver, ASCP_MIN_VERSION) < 0:
        raise Exception("Found ascp version " + ascp_ver + " but " +
                        ASCP_MIN_VERSION + " required")
    return True

def get_ascp_env(password):
    """
    Get the environment dictionary after adding the ASPERA_SCP_PASS variable
    (and value) to it.
    """
    logger.debug("In get_ascp_env.")

    environment = os.environ.copy()
    if 'ASPERA_SCP_PASS' in environment:
        logger.info("Honoring previously set ASPERA_SCP_PASS environment variable.")
    else:
        if password != None:
            logger.info("Setting ASPERA_SCP_PASS environment variable.")
            environment['ASPERA_SCP_PASS'] = password

    return environment

def run_ascp(ascp_cmd, password, keyfile=None):
    """
    Run the ascp command, returning True for success or False for failure.
    """
    logger.debug("In run_ascp.")

    if keyfile:
        if not os.path.exists(keyfile):
            raise IOError(
                "Can't use private key. No such file or directory: " + keyfile)
        ascp_cmd = [ascp_cmd[0], "-i", keyfile] + ascp_cmd[1:]

    try:
        logger.debug("Command: %s", " ".join(ascp_cmd))
        process = subprocess.Popen(
            ascp_cmd,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=get_ascp_env(password)
        )

        logger.info("Beginning transfer.")
        (s_out, s_err) = process.communicate()
        rc = process.returncode
        logger.info("Invocation of ascp complete. Return code: %s.", str(rc))

        success = False

        if rc == 0:
            logger.info("Aspera ascp utility returned successful exit value.")
            success = True
        else:
            if re.match(r"^.*failed to authenticate", s_err):
                logger.error("Aspera authentication failure.")
            else:
                if s_err != None:
                    logger.error("Unexpected STDERR from ascp: %s", s_err)
                if s_out != None:
                    logger.error("Unexpected STDOUT from ascp: %s", s_out)
    except subprocess.CalledProcessError as cpe:
        logger.error("Encountered an error when running ascp: %s", cpe)

    return success

def download_file(server, username, password, remote_path, local_path,
                  keyfile=None):
    """
    Download a single remote file using the aspera ascp utility.
    Returns True if successful, False if not.
    """
    logger.debug("In download_file.")

    check_ascp_version()
    ascp_cmd = [
        ASCP_COMMAND, "-T", "-v", "-l", "300M",
        username + "@" + server + ":" + remote_path,
        local_path
    ]

    return run_ascp(ascp_cmd, password, keyfile)

def upload_file(server, username, password, local_file, remote_path,
                keyfile=None):
    """
    Upload a single file with the Aspera ascp utility.
    Return True if successful, False if not.
    """
    logger.debug("In upload_file.")
    check_ascp_version()

    # check that local file exists
    if not os.path.isfile(local_file):
        logger.warn("local file " + local_file + " does not exist")
        return False

    remote_clause = username + "@" + server + ":" + remote_path
    ascp_cmd = [ASCP_COMMAND, "-T", "-v", "-l", "300M", local_file, remote_clause]

    return run_ascp(ascp_cmd, password, keyfile)
