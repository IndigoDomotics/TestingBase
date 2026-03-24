"""
Stuff that's shared across all the various tests.
"""
import json
import logging
import pathlib
import subprocess
import sys
import warnings
from datetime import timedelta, datetime
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
indigo.server.log(f"str_to_bool('{val}')", type="TestingBase", level=logging.DEBUG);
return json.dumps(utils.str_to_bool('{val}'))
"""
    return json.loads(run_host_script(script))

def reverse_bool_str_value(val: str) -> str:
    """
    Return the opposite boolean string value of the supplied string. We call IPH3 to do the conversion so we're sure
    that the value is what the IOM would generate. The script encodes in JSON then unencodes the result is decoded
    so that we don't have to eval() it.

    :param val: a string representing a boolean value
    :return: a JSON string representing the opposite boolean value
    """
    script: str = f"""
import utils, json, logging
indigo.server.log(f"reverse_bool_str_value('{val}')", type="TestingBase", level=logging.DEBUG);
return json.dumps(utils.reverse_bool_str_value('{val}'))
"""
    return json.loads(run_host_script(script))

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
    return pathlib.PosixPath(run_host_script(script))

def run_host_script(script: str) -> str:
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

def within_time_tolerance(datetime1, datetime2, tolerance_seconds: int = 1, raise_exc: bool = False) -> bool:
    """Check if two datetime objects are within specified seconds of each other"""
    if not isinstance(datetime1, datetime):
        datetime1 = datetime.fromisoformat(datetime1)
    if not isinstance(datetime2, datetime):
        datetime2 = datetime.fromisoformat(datetime2)
    return_val = abs(datetime1 - datetime2) <= timedelta(seconds=tolerance_seconds)
    if raise_exc:
        raise AssertionError(datetime1, datetime2, "time comparison failed")
    return return_val

def compare_dicts(
        dict1: dict, dict2: dict,
        exclude_keys: Optional[list] = None) -> bool:
    """
    This function checks if two dictionaries are equal. You can explicitly exclude certain keys and you can specify
    a list of datetime instances and specify a time tolerance in seconds.
    :param dict1: a dictionary, usually the dictionary that was generated through operations
    :param dict2: a dictionary, usually one created manually for testing purposes which is the expected results
    :param exclude_keys: a list of keys to exclude from comparison
    :param datetime_tolerance_list: a list of field names to compare as datetime instances within a tolerance in seconds
    :return: bool
    """
    if exclude_keys is not None:
        # First, create two filtered versions of the dicts and compare - if they aren't the same we can just return
        # False since we don't need to do anything else.
        filtered_dict1 = {k: v for k, v in dict1.items() if k not in exclude_keys}
        filtered_dict2 = {k: v for k, v in dict2.items() if k not in exclude_keys}
        return filtered_dict1 == filtered_dict2
    else:
        return dict1 == dict2


class SoftAssertionWarning(UserWarning):
    pass
