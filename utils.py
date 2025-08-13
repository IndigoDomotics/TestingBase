"""
Stuff that's shared across all the various tests.
"""
import logging
import sys
import subprocess
import pathlib
import json
from typing import Optional

# This will be the standard logging format for all the logging in the tests.
HANDLER: logging.Handler = logging.StreamHandler(sys.stdout)
pfmt = logging.Formatter(
    '%(levelname)s\t%(name)s.%(funcName)s:\t%(msg)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
HANDLER.setFormatter(pfmt)

####################
# The following are wrappers around the IOM utility functions so that we'll get consistent results
####################
def str_to_bool(val: str) -> bool:
    """
    Return the boolean value of the supplied string. We call IPH3 to do the conversion so we're sure
    that the boolean is what the IOM would generate. The script encodes in JSON then unencodes the result is decoded
    so that we don't have to eval() it.

    :param val: a string representing a boolean value
    :return: a JSON string representing the opposite boolean value
    """
    script: str = f"""
import utils, json, logging
indigo.server.log(f"str_to_bool({str})", type="TestingBase", level=logging.DEBUG);
return json.dumps(utils.str_to_bool('{val}'))
"""
    return json.loads(_run_host_script(script))

def reverse_bool_str_value(val: str) -> bool:
    """
    Return the opposite boolean string value of the supplied string. We call IPH3 to do the conversion so we're sure
    that the value is what the IOM would generate. The script encodes in JSON then unencodes the result is decoded
    so that we don't have to eval() it.

    :param val: a string representing a boolean value
    :return: a JSON string representing the opposite boolean value
    """
    script: str = f"""
import utils, json, logging
indigo.server.log(f"reverse_bool_str_value({str})", type="TestingBase", level=logging.DEBUG);
return json.dumps(utils.reverse_bool_str_value('{val}'))
"""
    return json.loads(_run_host_script(script))

def get_install_folder() -> pathlib.PosixPath:
    """
    Return the installation folder path for the running Indigo Server.

    :return: the posix path to the installation folder
    """
    script: str = """
import logging
indigo.server.log("getting install folder", type="TestingBase", level=logging.DEBUG);
return indigo.server.getInstallFolderPath()
"""
    return pathlib.PosixPath(_run_host_script(script))

def _run_host_script(script: str) -> str:
    """
    This will run the given script in the local IndigoPluginHost3 process and return the result. The reply will always
    be a string, so unless what you are calling returns a string, you should JSON encode it then decode it when this
    function returns.

    :param script: string containing the IOM script to run
    :return: string containing the result
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["/usr/local/indigo/indigo-host", "-e", script],
        stdout=subprocess.PIPE
    )
    return result.stdout.decode("utf8").strip("\n")
