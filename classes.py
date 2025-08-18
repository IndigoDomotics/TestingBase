import logging
import os
import subprocess
import time
import unittest
import enum
import json
from typing import Optional, Union, Type, Any
from abc import ABC

try:
    import dotenv
except ModuleNotFoundError:
    print("you must have dotenv installed")

try:
    import httpx
except ModuleNotFoundError:
    print("you must have httpx installed")

from .utils import get_install_folder, HANDLER

DEFAULT_TIMEOUT = 5.0  # This is the default for httpx

class WebhookStatusCode(enum.IntEnum):
    GOOD = 200  # Webhook completed successfully
    BAD_REQUEST = 400  # Webhook didn't supply JSON when it was configured for JSON
    MISSING = 404  # Webhook ID isn't defined
    BAD_METHOD = 405  # Webhook using a method other than what was configured
    SERVER_ERROR = 500  # Unexpected exception happened during processing - will write error and stack trace to log
    DISABLED = 503  # Webhook ID exists but is disabled


class APIBase(unittest.TestCase, ABC):
    """
    This is the base class for all tests in the various repos. It provides all the plumbing to talk to the Indigo Server
    via the HTTP API. It also provides some simplified methods to do common tasks.
    """
    # We define the logger class variable here so that we can access it both in normal methods as self.logger and in
    # class methods as cls.logger. We will actually get the logger and set attributes in the __init__ method.
    logger: logging.Logger = None

    @classmethod
    def setUpClass(cls):
        """
        These are things that are set up once for the class - all tests will share this stuff and it will only get
        called once for all tests.

        :return: None
        """
        print("setting up base class")
        cls._install_folder = get_install_folder()
        # We always look for a good API key to use for all HTTP communication
        cls.good_api_key: str = cls._get_shared_env_var("GOOD_API_KEY")
        # This is the URL prefix - like https://localhost:8176 or https://myreflector.indigodomo.net
        cls.url_prefix: str = f"{cls._get_shared_env_var('URL_PREFIX')}"
        # This is the full URL to the HTTP API
        cls.api_prefix: str = f"{cls.url_prefix}/v2/api"
        # This is the ID of the plugin that is being tested - in case you want to restart it while testing
        cls.plugin_id: str = cls._get_shared_env_var("PLUGIN_ID")
        # If you do restart, do you want to restart it in the debugger?
        cls.restart_plugin_in_debugger: bool = cls._get_shared_env_var("RESTART_IN_DEBUGGER", expected_type=bool)
        # When you restart, wait this many seconds before continuing. This will give the plugin enough time to get
        # fully started.
        cls.wait_time: int = cls._get_shared_env_var("PLUGIN_RESTART_WAIT_TIME", expected_type=int)
        # While print() statements work while running tests, using a logger is a better solution

    def __init__(self, methodName: str, env_path: str = ".env") -> None:
        """
        Init for the base class.

        :param methodName: the method name to run
        :param env_path: the path to the .env file, by default we'll just look in the current working directory
        :return: None
        """
        super(APIBase, self).__init__(methodName)
        # Load the file containing the environment variables for the user's install
        dotenv.load_dotenv(env_path)
        # Get the base class and set the logger to the logger variable - the one defined above.
        base_class = self.__class__.__bases__[0]
        base_class.logger = logging.getLogger(self.__class__.__name__)
        # Now, self.logger is the same as __class__.logger so you can use that in the rest of the methods. If you
        # define your own class methods, they should still have access via cls.logger.
        self.logger.addHandler(HANDLER)
        try:
            self.logger.setLevel(eval(self._get_shared_env_var("LOGGING_LEVEL")))
        except:
            self.logger.setLevel(logging.INFO)

    @classmethod
    def restart_plugin(cls) -> None:
        """
        Use this function to restart a plugin. We're defaulting to settings for IWS, but it could be called with another
        plugin if we wanted to.

        :return: None
        """
        command_list: list = ["/usr/local/indigo/indigo-restart-plugin"]
        if cls.restart_plugin_in_debugger:
            command_list.append("-d")
        command_list.append(cls.plugin_id)
        subprocess.run(command_list)
        time.sleep(cls.wait_time)

    @classmethod
    def send_raw_message(cls,
                         message_dict: dict,
                         bearer_token: Optional[str] = None,
                         timeout: float = DEFAULT_TIMEOUT) -> httpx.Response:
        """ Send a message payload to the API and return the response object.

        :param message_dict: dictionary that contains the full/complete message to send
        :param bearer_token: a token to use for authentication - defaults to the configured shared.GOOD_API_KEY
        :param timeout: timeout in seconds as a float
        :return response: httpx.Response object
        """
        if bearer_token is None:
            bearer_token = cls.good_api_key
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"{cls.api_prefix}/command"
        cls.logger.info("...sending HTTP API command")
        return httpx.post(url, headers=headers, json=message_dict, verify=False, timeout=timeout)

    @classmethod
    def send_simple_command(cls,
                            message_id: str,
                            message: str,
                            object_id: int,
                            parameters: Optional[dict] = None,
                            bearer_token: Optional[str] = None,
                            timeout: float = DEFAULT_TIMEOUT) -> httpx.Response:
        """ A simple method to create a message payload.

        :param message_id: the ID to pass through in the message - required in this method
        :param message: the message type, i.e. indigo.device.toggle
        :param object_id: id of an Indigo object (usually a device)
        :param parameters: a dict of optional parameters to send with the message
        :param bearer_token: a token to use for authentication - defaults to the configured shared.GOOD_API_KEY in
                             send_raw_message
        :param timeout: timeout in seconds as a float
        :return response: httpx.Response object
        """
        message_dict: dict = {
            "id": message_id,
            "message": message,
            "objectId": int(object_id)
        }
        if parameters is not None:
            message_dict["parameters"] = parameters
        return cls.send_raw_message(message_dict, bearer_token, timeout=timeout)

    @classmethod
    def get_indigo_object(cls,
                          endpoint: str,
                          obj_id: int = False,
                          bearer_token: str = None,
                          expected_status_code: int = 200,
                          timeout: float = DEFAULT_TIMEOUT) -> Union[dict, list, httpx.Response]:
        """
        Make httpx.get call to retrieve object props

        :param expected_status_code:
        :param endpoint: devices, variables, actionGroups, etc.
        :param obj_id: id of object to retrieve [optional]
        :param bearer_token: the API key to use for communication, will use self.api_key by default [optional]
        :param timeout: timeout in seconds as a float
        :return response: httpx.Response object
        """
        if bearer_token is None:
            bearer_token = cls.good_api_key
        url = f"{cls.api_prefix}/indigo.{endpoint}"
        headers = {'Authorization': f'Bearer {bearer_token}'}
        if obj_id:
            # get a specific object
            url += f"/{obj_id}"
        response = httpx.get(url, headers=headers, verify=False, timeout=timeout)
        if response.status_code != expected_status_code:
            raise AssertionError(response.status_code, expected_status_code, f"error getting indigo object: {response.text}")
        try:
            if response.status_code == 200:
                return_object = response.json()
            else:
                return_object = None
        except json.decoder.JSONDecodeError:
            raise AssertionError(f"error decoding indigo object: {response.text}")
        return return_object

    @classmethod
    def send_webhook(cls,
                     message_dict: dict,
                     webhook_id: str,
                     bearer_token: Optional[str],
                     timeout: float = DEFAULT_TIMEOUT
                     ) -> httpx.Response:
        """ Send a webhook and return the response object.

        :param message_dict: dictionary that contains the full/complete message to send
        :param webhook_id: the webhook ID from the webhook config - required in this method
        :param bearer_token: a token to use for authentication - defaults to the configured shared.GOOD_API_KEY
        :param timeout: timeout in seconds as a float
        :return response: httpx.Response object
        """
        url = f"{cls.url_prefix}/webhook/{webhook_id}"
        headers = dict()
        bearer_token = cls.good_api_key
        headers["Authorization"] = f"Bearer {bearer_token}"
        cls.logger.debug("sending webhook")
        if message_dict["method"] == "GET":
            response = httpx.get(url,
                                 headers=headers,
                                 params=message_dict.get("params", None),
                                 verify=False,
                                 timeout=timeout)
        elif message_dict["method"] == "POST" and message_dict.get("type", None) == "JSON":
            response = httpx.post(url,
                                  headers=headers,
                                  json=message_dict.get("params", None),
                                  verify=False,
                                  timeout=timeout)
        else:
            # default to HTTP FORM processing
            response = httpx.post(url,
                                  headers=headers,
                                  data=message_dict.get("params", None),
                                  verify=False,
                                  timeout=timeout)
        return response

    @classmethod
    def _get_testcase_env_var(cls,
                              var_name: str,
                              module: Optional[str] = None,
                              test_case_name: Optional[str] = None,
                              test_method_name: Optional[str] = None,
                              expected_type: Union[Type[str], Type[int], Type[bool]] = str,
                              default: Optional[any] = None
                              ) -> Any:
        if not module:
            module = cls.__module__
        if not test_case_name:
            test_case_name = cls.__name__
        var_specifier = f"{module}.{test_case_name}"
        if test_method_name:
            var_specifier += f".{test_method_name}"
        var_specifier += f".{var_name}"
        value = default
        try:
            value = os.environ[var_specifier]
        except:
            try:
                # Tweak the var_specifier to that it tries the name of the super class (WebhookTestBase for BadWebhookTests)
                test_case_name = cls.__bases__[0].__name__
                var_specifier = f"{module}.{test_case_name}"
                if test_method_name:
                    var_specifier += f".{test_method_name}"
                var_specifier += f".{var_name}"
                value = os.environ[var_specifier]
            except:
                pass
        if expected_type is int:
            try:
                return int(value)
            except ValueError:
                raise AssertionError(f"{value} could not be converted to int")
        elif expected_type is bool:
            try:
                decoded_val = json.loads(value.lower())
                if not isinstance(decoded_val, bool):
                    raise ValueError(f"{value} could not be converted to bool")
            except ValueError:
                raise AssertionError(f"{value} could not be converted to bool")
        return value

    @classmethod
    def _get_shared_env_var(cls,
                            var_name: str,
                            expected_type: Union[Type[str], Type[int], Type[bool]] = str,
                            default: Optional[any] = None
                            ) -> Any:
        value = default
        try:
            return os.environ[f"shared.{var_name}"]
        except:
            pass
        if expected_type is int:
            try:
                return int(value)
            except ValueError:
                raise AssertionError(f"{value} could not be converted to int")
        elif expected_type is bool:
            try:
                decoded_val = json.loads(value.lower())
                if not isinstance(decoded_val, bool):
                    raise ValueError(f"{value} could not be converted to bool")
            except ValueError:
                raise AssertionError(f"{value} could not be converted to bool")
        return value

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
