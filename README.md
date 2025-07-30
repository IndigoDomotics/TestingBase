# TestingBase

This repo contains the shared files used in tests across the Indigo repos. The ENV_TEMPLATE file has the necessary
environmental values that must be set up to use this base. You should add them to the .env file in the tests directory.

So here's how it works - let's say we're setting up the WebServerPlugin repo. The repo should be structured like this:

WebServerPlugin
    /docs
    /tests
        /shared   <- this is where you mount this submodule
        .env  <- this is where you set the environment vars specified in the template
        test_something.py  <- your test cases would subclass shared.utils.APIBase

In order to use this repo, you must have python-dotenv and httpx installed.