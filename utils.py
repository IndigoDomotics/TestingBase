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

def strtobool(val: str) -> bool:
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.

    :param val: the value to convert
    :return: bool
    """
    if isinstance(val, bool):
        return val
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
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
