Testing Guide

This repository bundles Django’s full test suite. Below are concise, practical instructions for running Python unit tests, Selenium browser tests (Chrome/chromedriver), and JavaScript tests via npm. Links to the upstream docs are included for deeper detail.

Prerequisites

- Python 3 with virtualenv available.
- Optional: Node.js and npm for JavaScript tests.
- Optional: Google Chrome and matching chromedriver for Selenium.

Quickstart: Python unit tests (SQLite)

1) Create and activate a virtual environment.
2) Install Django in editable mode and test requirements.
3) Run the test runner.

```
cd tests
python -m pip install -e ..
python -m pip install -r requirements/py3.txt
./runtests.py
```

Database setup notes (PostgreSQL/MySQL/etc.)

The default test settings use SQLite (tests/test_sqlite.py). To run against another backend, provide your own settings module and point the runner to it with --settings or DJANGO_SETTINGS_MODULE.

Requirements for non-SQLite backends:

- Define two databases in DATABASES: default and other (same backend, different NAME).
- Ensure the database user can CREATE DATABASE (for test DB creation).
- UTF-8 default charset (or set TEST_CHARSET to UTF-8 in the test settings).

Example: PostgreSQL test settings

```
# tests/settings_postgres.py

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "django",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    },
    "other": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "django_other",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    },
}
```

Run the suite with these settings:

```
cd tests
./runtests.py --settings=tests.settings_postgres
# or
DJANGO_SETTINGS_MODULE=tests.settings_postgres ./runtests.py
```

Selenium tests (Chrome + chromedriver)

Django’s Selenium tests live in the Python test suite and are tagged "selenium". The runner provides flags to select browsers, use headless mode, and point to a Selenium Hub if desired.

Install requirements:

- Python deps: selenium is included in tests/requirements/py3.txt.
- Browser: Google Chrome (or Chromium).
- Driver: chromedriver matching your Chrome version. Install via your OS package manager or from the official chromedriver site; ensure chromedriver is on PATH.

Common commands:

```
cd tests
python -m pip install -r requirements/py3.txt

# Run Selenium tests on Chrome; add --headless to avoid opening a browser.
./runtests.py --selenium=chrome --parallel=1
./runtests.py --selenium=chrome --headless --parallel=1

# If using a Selenium Hub, provide hub URL and external host.
./runtests.py --selenium=chrome \
              --selenium-hub=http://localhost:4444 \
              --external-host=YOUR_HOSTNAME \
              --parallel=1
```

Notes:

- When --selenium is used, the runner automatically includes the "selenium" tag. You can also use --screenshots to capture UI screenshots during Selenium tests.
- Parallel limitation: on systems using the "spawn" start method, Selenium requires --parallel=1.

JavaScript tests (npm + QUnit)

JavaScript tests are in js_tests/. They use QUnit and run via Grunt. Ensure Node.js and npm are installed.

Commands:

```
# At repo root
npm install
npm test

# Manual in-browser run (helpful for debugging):
# Serve repo root and open js_tests/tests.html in a browser.
```

References

- Python unit tests: docs/internals/contributing/writing-code/unit-tests.txt
- JavaScript tests: docs/internals/contributing/writing-code/javascript.txt
- Selenium test support: django/test/selenium.py and tests/runtests.py (see --selenium, --headless, --selenium-hub, --external-host)

