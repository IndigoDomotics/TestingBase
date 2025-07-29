"""
Stuff that's shared across all the various tests.
"""
import logging
import sys
import subprocess
import time
import pathlib
import unittest
import os
from typing import Optional

try:
    import dotenv
except ModuleNotFoundError:
    sys.path.insert(0, "../Web Server.indigoPlugin/Contents/Packages")
    import dotenv

try:
    import httpx
except ModuleNotFoundError:
    sys.path.insert(0, "../Web Server.indigoPlugin/Contents/Packages")
    import httpx

# We need the hardcoded string from the plugin.py file so that we can test with it included and not included.
# try:
#     from ../constants import DO_NOT_USE_API_KEYS
# except ModuleNotFoundError:
#     sys.path.insert(0, "../Web Server.indigoPlugin/Contents/Server Plugin")
#     from constants import DO_NOT_USE_API_KEYS

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


class APIBase(unittest.TestCase):
    """
    This is the base class for all tests in the various repos. It provides all the plumbing to talk to the Indigo Server
    via the HTTP API. It also provides some simplified methods to do common tasks such as
    """

    @classmethod
    def setUpClass(cls):
        print("setting up base class")
        cls._install_folder = get_install_folder()

    def __init__(self, methodName: str) -> None:
        """
        Setup shared by all tests.

        :return: None
        """
        super(APIBase, self).__init__(methodName)
        # Look in the directory above for the .env file. This repo should be a submodule mounted at the
        #  REPO/tests/shared
        # directory and then used appropriately.
        dotenv.load_dotenv("..")
        self.good_api_key: str = self._get_shared_env_var("GOOD_API_KEY")
        self.url_prefix: str = f"{self._get_shared_env_var('URL_PREFIX')}/"
        self.api_prefix: str = f"{self.url_prefix}/v2/api"
        self.plugin_id: str = self._get_shared_env_var("PLUGIN_ID")
        self.restart_plugin_in_debugger: bool = strtobool(self._get_shared_env_var("RESTART_IN_DEBUGGER"))
        self.wait_time: int = self._get_shared_env_var("PLUGIN_RESTART_WAIT_TIME")
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.logger.addHandler(HANDLER)
        try:
            self.logger.setLevel(eval(self._get_shared_env_var("LOGGING_LEVEL")))
        except:
            self.logger.setLevel(logging.INFO)

    def restart_plugin(self) -> None:
        """
        Use this function to restart a plugin. We're defaulting to settings for IWS, but it could be called with another
        plugin if we wanted to.

        :return: None
        """
        command_list: list = ["/usr/local/indigo/indigo-restart-plugin"]
        if self.restart_plugin_in_debugger:
            command_list.append("-d")
        command_list.append(self.plugin_id)
        subprocess.run(command_list)
        time.sleep(self.wait_time)

    def send_raw_message(self, message_dict: dict, bearer_token: Optional[str] = None) -> httpx.Response:
        """ Send a message payload to the API and return the response object.

        :param message_dict: dictionary that contains the full/complete message to send
        :param bearer_token: a token to use for authentication - defaults to the configured shared.GOOD_API_KEY
        :return response: httpx.Response object
        """
        if bearer_token is None:
            bearer_token = self.good_api_key
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"{self.api_prefix}/command"
        self.logger.info("...sending HTTP API command")
        return httpx.post(url, headers=headers, json=message_dict, verify=False)

    def send_simple_command(self,
                            message_id: str,
                            message: str,
                            object_id: int,
                            parameters: Optional[dict] = None,
                            bearer_token: Optional[str] = None
                            ) -> httpx.Response:
        """ A simple method to create a message payload.

        :param message_id: the ID to pass through in the message - required in this method
        :param message: the message type, i.e. indigo.device.toggle
        :param object_id: id of an Indigo object (usually a device)
        :param parameters: a dict of optional parameters to send with the message
        :param bearer_token: a token to use for authentication - defaults to the configured shared.GOOD_API_KEY in
                             send_raw_message
        :return response: httpx.Response object
        """
        message = {
            "id": message_id,
            "message": message,
            "objectId": int(object_id)
        }
        if parameters is not None:
            message["parameters"] = parameters
        return self.send_raw_message(message, bearer_token)

    def get_indigo_object(self, endpoint: str, obj_id: int = False, bearer_token: str = None) -> httpx.Response:
        """
        Make httpx.get call to retrieve object props

        :param endpoint: devices, variables, actionGroups, etc.
        :param obj_id: id of object to retrieve [optional]
        :return response: httpx.Response object
        """
        if bearer_token is None:
            bearer_token = self.good_api_key
        url = f"{self.api_prefix}/indigo.{endpoint}"
        headers = {'Authorization': f'Bearer {self.good_api_key}'}
        if obj_id:
            # get a specific object
            url += f"/{obj_id}"
        response = httpx.get(url, headers=headers, verify=False)
        return response

    def _get_testcase_env_var(self,
                              var_name: str,
                              module: Optional[str] = None,
                              test_case_name: Optional[str] = None,
                              test_method_name: Optional[str] = None,
                              default: Optional[any] = None
                              ) -> any:
        if not module:
            module = self.__module__
        if not test_case_name:
            test_case_name = self.__class__.__name__
        var_specifier = f"{module}.{test_case_name}"
        if test_method_name:
            var_specifier += f".{test_method_name}"
        var_specifier += f".{var_name}"
        try:
            return os.environ[var_specifier]
        except:
            try:
                # Tweak the var_specifier to that it tries the name of the super class (WebhookTestBase for BadWebhookTests)
                return os.environ[var_specifier]
            except:
                if default is not None:
                    return default
                raise

    def _get_shared_env_var(self, var_name: str, default: Optional[any] = None) -> any:
        try:
            return os.environ[f"shared.{var_name}"]
        except:
            if default is not None:
                return default
            raise

    def setUp(self) -> None:
        super(APIBase, self).setUp()
        self.logger.info("Setting up test...")

    def tearDown(self) -> None:
        """
        Tear down shared by all tests. Any subclasses that implement their own tearDown function should call this
        superclass method because of the need to wait on logging to complete before finishing.

        :return: None
        """
        super(APIBase, self).tearDown()
        self.logger.info("...Tearing down test")
        # We add this little sleep to make sure that all test logging happens before the test result summary is shown
        time.sleep(1)
