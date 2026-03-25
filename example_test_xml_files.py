"""
Example test file - don't attempt to run this file directly.

This file contains examples for each of the XML files that can be part of a standard Indigo plugin. I do a little bit of
magic to get the path correct. The assumption is that your repo is constructed something like this:

MyPluginRepo/
    tests/
        shared/
        test_xml_files.py  # can be named anything
    MyPlugin.indigoPlugin/
        Contents/
            Server Folder/
                Actions.xml
                Devices.xml
                Events.xml
                MenuItems.xml
                PluginConfig.xml

You can of course just insert the correct path to the file your setup is different.

Of course, most plugins only use a subset of the config ui files, so you only need to test the ones that you use in your
plugin.

To run your tests, in Terminal run this test with:
    > cd <path/to/repo/root/>
    > python -m unittest test_xml.TestActionsXml
"""
import os

from .classes import APIBase, ValidateXmlFile

# Construct the path to the server plugin directory given the assumption above.
#    This would result in a path like: /Users/me/MyPluginRepo/MyPlugin.indigoPlugin/Contents/Server Folder
# because the hardcoded path is relative to the location of this file and os.path.abspath() will adjust to make it
# the correct full path.
SERVER_PLUGIN_DIR_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../MyPlugin.indigoPlugin/Contents/Server Plugin"
    )
)

class TestDeviceXml(ValidateXmlFile, APIBase):
    server_plugin_dir_path = SERVER_PLUGIN_DIR_PATH
    file_name = "Devices.xml"

class TestActionsXml(ValidateXmlFile, APIBase):
    server_plugin_dir_path = SERVER_PLUGIN_DIR_PATH
    file_name = "Actions.xml"

class TestEventsXml(ValidateXmlFile, APIBase):
    server_plugin_dir_path = SERVER_PLUGIN_DIR_PATH
    file_name = "Events.xml"

class TestMenuItemsXml(ValidateXmlFile, APIBase):
    server_plugin_dir_path = SERVER_PLUGIN_DIR_PATH
    file_name = "MenuItems.xml"

class TestPluginConfigXml(ValidateXmlFile, APIBase):
    server_plugin_dir_path = SERVER_PLUGIN_DIR_PATH
    file_name = "PluginConfig.xml"
