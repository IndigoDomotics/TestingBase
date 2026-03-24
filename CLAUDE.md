# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TestingBase is a git submodule providing shared testing infrastructure for [Indigo](https://www.indigodomo.com/) plugin repos. It is mounted at `tests/shared` in consumer repos. It communicates with a running Indigo Server via its HTTP API and the local `indigo-host` CLI tool.

## Installation

Dependencies listed in `module-requirements.txt`:
```
pip install python-dotenv httpx==0.25.2
```

## Running Tests

Tests live in the consumer repo (e.g. `WebServerPlugin/tests/`), not in this repo. Tests are run from the consumer repo's `tests/` directory:

```bash
python -m unittest test_something.py              # run a test file
python -m unittest test_something.TestClass       # run a test class
python -m unittest test_something.TestClass.test_method  # run a single test
```

## Architecture

### Module structure

- `__init__.py` — exports `APIBase` and `WebhookStatusCode` for consumer import via `from shared import APIBase`
- `classes.py` — core classes: `APIBase` (abstract `unittest.TestCase` subclass) and `WebhookStatusCode` enum
- `utils.py` — standalone utility functions

### `APIBase` class (`classes.py`)

Abstract base class combining `unittest.TestCase` and `ABC`. All API interaction methods are **class methods** (accessible as `self.method()` in tests).

**Setup flow:**
1. `__init__` loads `.env` via `python-dotenv` (default path: `../` relative to test file, configurable)
2. `setUpClass` reads shared env vars and sets `cls.good_api_key`, `cls.url_prefix`, `cls.api_prefix`, `cls.plugin_id`, etc.
3. `tearDown` must call `super()` — adds a 1-second sleep so logs flush before test summary

**Key methods:**
- `send_raw_message(message_dict)` — POST to `/v2/api/command` with Bearer auth
- `send_simple_command(message_id, message, object_id, parameters)` — constructs and sends a command dict
- `get_indigo_object(endpoint, obj_id)` — GET from `/v2/api/indigo.<endpoint>[/<obj_id>]`
- `set_variable(message_id, variable, new_value)` — sends `indigo.variable.updateValue` command
- `send_webhook(message_dict, webhook_id, bearer_token)` — sends GET or POST to `/webhook/<webhook_id>`
- `restart_plugin()` — calls `/usr/local/indigo/indigo-restart-plugin` subprocess
- `_get_shared_env_var(var_name, expected_type, default)` — reads `shared.<var_name>` from env
- `_get_testcase_env_var(var_name, ...)` — reads `<module>.<TestClass>[.<method>].<var_name>` from env

### Environment variable conventions

Env vars are namespaced. Copy `ENV_TEMPLATE` to `.env` in the consumer repo's `tests/` directory:

- `shared.<VAR_NAME>` — shared across all test cases (read by `_get_shared_env_var`)
- `<module>.<TestClass>.<var_name>` — test-class-specific (read by `_get_testcase_env_var`)
- `<module>.<TestClass>.<method>.<var_name>` — test-method-specific

### `utils.py`

Standalone functions that wrap Indigo server calls:
- `run_host_script(script)` — executes a Python script in the local `indigo-host` process (`/usr/local/indigo/indigo-host -e <script>`), returns stdout as string
- `get_install_folder()` — returns install path via `run_host_script`; cached in `cls._install_folder` at `setUpClass` time
- `str_to_bool(val)` / `reverse_bool_str_value(val)` — delegate to IOM via `run_host_script` for consistent boolean handling
- `within_time_tolerance(dt1, dt2, tolerance_seconds=1)` — compares two datetimes within a tolerance
- `compare_dicts(dict1, dict2, exclude_keys)` — dict equality with optional key exclusion

**Performance note:** Each `run_host_script` call spawns a new IPH3 process — cache results at `setUpClass` time when the same value is needed across multiple tests.

## Submodule management

Update this submodule in a consumer repo:
```bash
git submodule update --recursive --remote tests/shared
```

Do not commit changes to this repo from consumer repos — changes should go through the canonical TestingBase repo.
