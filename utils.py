"""
Stuff that's shared across all the various tests.
"""
import logging
import sys
import subprocess
import pathlib

# This will be the standard logging format for all the logging in the tests.
HANDLER: logging.Handler = logging.StreamHandler(sys.stdout)
pfmt = logging.Formatter(
    '%(levelname)s\t%(name)s.%(funcName)s:\t%(msg)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
HANDLER.setFormatter(pfmt)

####################
# The following are direct copies from the Py3Libraries/utils.py file in the IndigoProj repo.
####################
BOOL_MAP_TRUE: dict[str, str] = {
    "y": "n",
    "yes": "no",
    "t": "f",
    "true": "false",
    "on": "off",
    "1": "0",
    "open": "closed",
    "locked": "unlocked",
}

BOOL_MAP_FALSE: dict[str, str] = {v: k for k, v in BOOL_MAP_TRUE.items()}

def str_to_bool(val: str) -> bool:
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.

    This is directly from distutils.util.strtobool, but replicated here
    because it's deprecated in python 3.12.

    I've added open/closed and locked/unlocked.

    :param val: the value to convert
    :return: bool
    """
    if isinstance(val, bool):
        return val
    val = val.lower()
    if val in BOOL_MAP_TRUE.keys():
        return True
    elif val in BOOL_MAP_FALSE.keys():
        return False
    else:
        raise ValueError(f"invalid truth value: '{val}'")

def reverse_bool_str_value(val: str) -> str:
    """
    Return the opposite boolean string value of the supplied string.

    :param val: a string representing a boolean value
    :return: a string representing the opposite boolean value
    """
    if isinstance(val, bool):
        return str(not val)
    if val in BOOL_MAP_TRUE.keys():
        return BOOL_MAP_TRUE[val]
    elif val in BOOL_MAP_FALSE.keys():
        return BOOL_MAP_FALSE[val]
    else:
        raise ValueError(f"invalid truth value: '{val}'")

def get_install_folder() -> pathlib.PosixPath:
    """
    Return the installation folder path for the running Indigo Server.

    :return: the posix path to the installation folder
    """
    result: subprocess.CompletedProcess = subprocess.run(
        ["/usr/local/indigo/indigo-host", "-e",
         'indigo.server.log("getting install folder"); return indigo.server.getInstallFolderPath()'],
        stdout=subprocess.PIPE
    )
    return pathlib.PosixPath(result.stdout.decode("utf8").strip("\n"))
