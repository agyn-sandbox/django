Prerequisites:
- Python >= 3.11; pip
- Dependencies: -r tests/requirements/py3.txt
- Optional: Chrome/chromedriver for Selenium; npm for JS tests

Setup:
- pip install -r tests/requirements/py3.txt

Run tests:
- Unit: python -Wall tests/runtests.py -v2
- Selenium (SQLite): python -Wall tests/runtests.py --noinput --selenium=chrome --headless --settings=test_sqlite
- JS: npm test

Troubleshooting:
- Ensure Chrome + chromedriver installed for Selenium; DB services required for Postgres/MySQL/Oracle tests.

