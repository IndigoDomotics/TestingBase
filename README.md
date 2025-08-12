# TestingBase

This repo contains the shared files used in tests across the Indigo repos. The `ENV_TEMPLATE` file has the necessary
environmental values that must be set up to use this base. This repo uses the python-dotenv package to read in
environment values from a `.env` file. By default, we assume that the .env file resides in the parent directory, in 
our case `tests`, though you can specify the location in the init method.

So here's how it works - let's say we're setting up the WebServerPlugin repo. The repo should be structured like this:

```
WebServerPlugin
+- docs
+- tests
  +- shared   <- this is where you mount this submodule
  +- .env  <- this is where you set the environment vars specified in the template
  +- test_something.py  <- your test cases would subclass shared.utils.APIBase
```
### Python package requirements

In order to use this repo, you must have `python-dotenv` and `httpx` installed. The `testing-requirements.txt` file is 
always going to have the correct packages needed by this module.

## Installing and Updating the submodule

### Adding the TestingBase submodule to one of the Indigo repos

If you are checking out one of the IndigoDomotics repos, it's very likely that we've already added the submodule. You 
can tell by looking for the `.gitmodules` file at the top level of the repo. It may look something like this:

```aiignore
[submodule "tests/shared"]
	path = tests/shared
	url = https://github.com/IndigoDomotics/TestingBase.git
```

If that file is there and contains the `tests/shared` submodule definition, you'll need to init it from the command 
line:

`git submodule update --init`

That should get the initial repo. Then you can just jump down to the 
**[Updating the TestingBase submodule in your repo]()** section to update the repo as necessary.

### Adding the TestingBase submodule to your own repo

If your repo doesn't already have the submodule defined as outlined above, do this (assuming that you are at the top 
level of your repo and that your unit tests are in the tests directory):

`git submodule add https://github.com/IndigoDomotics/TestingBase.git tests/shared`

That will check out the repo as the tests/shared directory. This will create the `.gitmodules` file discussed above.
You can now use the features of this repo in your tests.

### Updating the TestingBase submodule in your repo

If there are changes to the this repo, you will also need to update it from the command line in your local repos (again,
if you are at the top level of your repo and you put the submodule in the tests/shared directory):

`git submodule update --recursive --remote tests/shared`

You can, of course, put the submodule anywhere you want, but for standardization purposes, we highly encourage users
of this repo to follow the structure above.

Note: do not update your copy of the testing module. If you need changes, please contact Indigo Support and we'll 
discuss how best to satisfy your needs.

## Using the TestingBase repo

The most basic usage of this submodule is to use the `APIBase` class as the super class for your test cases:

```aiignore
from shared import APIBase

class MyTestCase(APIBase):
    def __init__(self, methodName: str) -> None:
        # If you want dotenv to look for a .env file somewhere else, pass the path here. The default
        # is the current working directory so you can just not pass anything for the second arg.
        super(APIBase, self).__init__(methodName, "/my/custom/path/to/.env")
```

