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

### Adding the TestingBase submodule to your repo

All test cases now should inherit from this repo, which should be included as a submodule. PyCharm doesn't integrate 
git submodules in any way, so you'll need to revert to a terminal window to maintain the submodule. When you first 
check out the repo, or if you have one that's already local but you haven't yet added the testing base, do this:

`git submodule add https://github.com/IndigoDomotics/TestingBase.git tests/shared`

That will check out the repo as the tests/shared directory. Note that all of the tests should use the APIBase test case 
class, so you will need to do this before running any tests.

If there are changes to the this repo, you will also need to update it from the command line in your local repos:

`git submodule update --recursive --remote tests/shared`

