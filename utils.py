"""
Stuff that's shared across all the various tests.
"""
import logging
import sys
import subprocess
import pathlib
import json
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

def within_time_tolerance(datetime1, datetime2, tolerance_seconds: int = 1) -> bool:
    """Check if two datetime objects are within specified seconds of each other"""
    return abs(datetime1 - datetime2) <= timedelta(seconds=tolerance_seconds)

def compare_dicts(
        dict1: dict, dict2: dict,
        exclude_keys: Optional[list] = None,
        datetime_tolerance_list: Optional[list] = None) -> bool:
    are_equal = True
    if exclude_keys is not None:
        # First, create two filtered versions of the dicts and compare - if they aren't the same we can just return
        # False since we don't need to do anything else.
        filtered_dict1 = {k: v for k, v in dict1.items() if k not in exclude_keys}
        filtered_dict2 = {k: v for k, v in dict2.items() if k not in exclude_keys}
        if filtered_dict1 != filtered_dict2:
            return False
    # If the filtered dicts are the same, then we want to cycle through the datetime tolerance map and convert and
    # compare them. Each entry in the map is something like this:
    #   ("timestamp", "some_other_datetime", 1)
    # The value in dict1 with the appropriate key should match the value in dict2 with the key within the specified
    # using tolerance in seconds. In the above example, this call will be made:
    #    within_time_tolerance(dict1["timestamp"], dict2["some_other_datetime"], 1)
    # If either of the values from the dicts are strings, I'll assume that they are ISO format and will use
    # datetime.fromisoformat(value) to attempt a conversion first.
    if datetime_tolerance_list is not None:
        for key1, key2, tolerance in datetime_tolerance_list:
            datetime1 = dict1[key1]
            if not isinstance(datetime1, datetime):
                # Assume ISO format string
                datetime1 = datetime.isoformat(datetime1)
            datetime2 = dict2[key2]
            if not isinstance(datetime2, datetime):
                # Assume ISO format string
                datetime2 = datetime.isoformat(datetime2)
            are_equal = within_time_tolerance(datetime1, datetime2, tolerance)
    return are_equal
