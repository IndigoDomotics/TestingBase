import logging
import os
import subprocess
import time
import unittest
from typing import Optional
from abc import ABC

try:
    import dotenv
except ModuleNotFoundError:
    print("you must have dotenv installed")

try:
    import httpx
except ModuleNotFoundError:
    print("you must have httpx installed")

from .utils import get_install_folder, strtobool, HANDLER

class APIBase(unittest.TestCase, ABC):
    """
    This is the base class for all tests in the various repos. It provides all the plumbing to talk to the Indigo Server
    via the HTTP API. It also provides some simplified methods to do common tasks.
    """
    @classmethod
    def setUpClass(cls):
        """
        This is a class method because it requires running a script against the installed IndigoPluginHost process in
        order to get the install directory. We just want to run it once before the first test case and remember it for
        the rest.

        :return: None
        """
        print("setting up base class")
        cls._install_folder = get_install_folder()

    def __init__(self, methodName: str, env_path: str = ".") -> None:
        """
        Init for the base class.

        :param methodName: the method name to run
        :param env_path: the path to the .env file, by default we'll look at the parent directory
        :return: None
        """
        super(APIBase, self).__init__(methodName)
        # Load the file containing the environment variables for the user's install
        dotenv.load_dotenv(env_path)
        # We always look for a good API key to use for all HTTP communication
        self.good_api_key: str = self._get_shared_env_var("GOOD_API_KEY")
        # This is the URL prefix - like https://localhost:8176 or https://myreflector.indigodomo.net
        self.url_prefix: str = f"{self._get_shared_env_var('URL_PREFIX')}"
        # This is the full URL to the HTTP API
        self.api_prefix: str = f"{self.url_prefix}/v2/api"
        # This is the ID of the plugin that is being tested - in case you want to restart it while testing
        self.plugin_id: str = self._get_shared_env_var("PLUGIN_ID")
        # If you do restart, do you want to restart it in the debugger?
        self.restart_plugin_in_debugger: bool = strtobool(self._get_shared_env_var("RESTART_IN_DEBUGGER"))
        # When you restart, wait this many seconds before continuing. This will give the plugin enough time to get
        # fully started.
        self.wait_time: int = self._get_shared_env_var("PLUGIN_RESTART_WAIT_TIME")
        # While print() statements work while running tests, using a logger is a better solution
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
        :param bearer_token: the API key to use for communication, will use self.api_key by default [optional]
        :return response: httpx.Response object
        """
        if bearer_token is None:
            bearer_token = self.good_api_key
        url = f"{self.api_prefix}/indigo.{endpoint}"
        headers = {'Authorization': f'Bearer {bearer_token}'}
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
