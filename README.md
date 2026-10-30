# **Playwright (Python) + Pytest Automation Framework**

A page-object-based UI automation framework built with **Playwright for Python** and **pytest**. This document explains the folder structure, why each part exists, the naming conventions, and the best practices every contributor should follow.

## 1. Folder Structure at a Glance

```text
project-root/
├── pages/                              # Page objects and locators, grouped by app
│   ├── base_page/
│   │   └── base_page.py                # Browser setup, shared actions, assertions
│   └── <app_name>/                     # Example: admin/
│       ├── <app>_<screen>_page.py      # Example: admin_access_management_page.py
│       └── ...
├── tests/                              # Test files, grouped by app
│   └── <app_name>/
│       ├── test_<app>_<screen>.py
│       └── test_<app>_<screen>_<feature>.py
├── test_data/                          # Test data, grouped by app
│   └── <app_name>/
│       ├── <app>_<screen>_test_data.json
│       ├── *.json
│       ├── *.txt
│       ├── *.csv
│       └── *.xlsx
├── utils/                              # Reusable helpers
│   ├── common_methods.py
│   ├── reports.py
│   ├── email_utils.py
│   ├── config.py
│   └── excel_utils.py
├── reports/                            # Generated reports, screenshots, and logs
│   └── screenshots/
├── automation_control_sheet.xlsx       # Controls which tests or suites run
├── conftest.py                         # Fixtures, setup/teardown, and hooks
├── pytest.ini                          # Pytest configuration and markers
├── .env                                # Local settings; do not commit
├── .gitignore
├── requirements.txt
└── README.md
```

**Rule for pages/, tests/ and test_data/:** each has one **subfolder per app** , named after the app (in lowercase snake_case). The app's .py files live inside that subfolder. The shared BasePage is the one exception to the app pattern: it has its own base_page/ subfolder under pages/.

## 2. Folder and File Responsibilities

## 2.1 `pages/`: Locators and Page Objects

**Purpose:** Holds one Page Object per application screen, **grouped in a subfolder named after the app** (e.g. pages/admin/). Each class contains that screen's **locators** and the **methods** (user actions) that operate on them.

**Why it matters:** If the UI changes, only one file needs to be updated, not every test. Tests stay readable and free of selectors.

**Location and naming:** pages/<app_name>/<app>_<screen>_page.py, e.g. pages/admin/admin_access_management_page.py.

### Inside Each Page File

1. **Header block** (author / created date / modified by / modified date)

2. **Locators** section, with clear comments describing which part of the screen each group belongs to

3. **Methods** section: actions and validations for that screen

```python
"""Page object for the Admin > Access Management screen.

Author: <name>
Created On: <dd-mm-yyyy>
Modified By: <name>
Modified On: <dd-mm-yyyy>
"""

from pages.base_page.base_page import BasePage

class AdminAccessManagementPage(BasePage):
    # LOCATORS: User listing grid
    ADD_USER_BUTTON = "button[data-testid='add-user']"
    SEARCH_INPUT = "input[placeholder='Search user']"

    # METHODS: User listing grid
    def click_add_user(self):
        self.click(self.ADD_USER_BUTTON)

    def search_user(self, name: str):
        self.fill(self.SEARCH_INPUT, name)
```

## 2.2 `pages/base_page/base_page.py`: The Foundation Class

**Purpose:** A single parent class that every page object inherits from. It lives in its own subfolder, pages/base_page/, containing base_page.py. It wraps Playwright so that no test or page object calls raw Playwright APIs directly.

|Section|What it contains|
|---|---|
|**Browser init**|Browser / context / page initialisation and shared setup|
|**Browser action methods**|open, click, hover, double_click, fill, select_dropdown, etc.|
|**Assertion methods**|is_visible, is_enabled / clickable, is_text_present, etc.|

**Why it matters:** Central place for waits, logging, retries and error handling. Improve it once and every page benefits.

## 2.3 `tests/`: Test Folder

**Purpose:** Contains **all** test files, **grouped in a subfolder named after the app** (e.g. tests/admin/). Nothing else (no helpers, no data) should live here.

**Location and naming:** tests/<app_name>/test_<appname>_<screenname>.py, e.g. tests/admin/test_admin_access_management_user.py. Variants for sub-features add a suffix: tests/admin/test_admin_access_management_user_xyz.py.

### Structure of Every Test File

1. **Header** (author, created, modified by, modified date)

2. **Scenario** description (what business flow the file covers)

3. **Test cases** , each decorated with markers (see section 4)

```python
"""Test the Admin > Access Management user-search flow.

Author: <name>
Created On: <dd-mm-yyyy>
Modified By: <name>
Modified On: <dd-mm-yyyy>
"""

import pytest
from pages.admin.admin_access_management_page import AdminAccessManagementPage

# Scenario: Admin creates, searches, and deactivates a user.
@pytest.mark.smoke
@pytest.mark.regression
def test_admin_can_search_user(page):
    access_page = AdminAccessManagementPage(page)
    access_page.search_user("john")
    assert access_page.is_visible(access_page.SEARCH_INPUT)
```

## 2.4 `test_data/`: Test Data

**Purpose:** Keeps data separate from test logic so the same test can run with different data sets. Data is **grouped in a subfolder named after the app** (e.g. test_data/admin/), mirroring pages/ and tests/.

**Location and naming:** test_data/<app_name>/<app>_<screen>_test_data.JSON or CSV or Xls for Python data modules; JSON, CSV and Excel files for the same app sit in the same subfolder.

**Used formats:** JSON, CSV, Excel.

|Format|Best used for|
|---|---|
|Python module|Small, static data and constants|
|JSON|Structured / nested payloads|
|CSV / Excel|Large data sets, data-driven (parametrised) tests|

## 2.5 `utils/`: Reusable Methods

**Purpose:** Generic helpers that are **independent of any particular screen** .

|File|Responsibility|
|---|---|
|common_methods.py|Shared helper functions (date handling, random data, string utilities)|
|reports.py|Report generation and screenshot handling|
|email_utils.py|Sending the execution report / summary by email|
|config.py|Reads settings from .env and exposes them to the framework|
|excel_utils.py|Reading/writing Excel files (test data, control sheet)|

Rule of thumb: if it knows about a specific screen, it belongs in pages/. If it works anywhere, it belongs in utils/.

## 2.6 `conftest.py`: Fixtures, Setups, and Configuration

**Purpose:** pytest's central hook file, auto-loaded before tests run.

Typical contents:

- Browser / context / page fixtures

- Login and logout setup/teardown

- Command-line options (e.g. --env, --browser, --headed)

- Hooks for screenshot-on-failure and report metadata

## 2.7 `.env`: Environment Configuration

**Purpose:** Holds environment-specific values that must **not** be hard-coded.

- List of application URLs (dev / QA / UAT)

- User ID / password for test accounts

• Email configuration (SMTP details, recipients) ```dotenv
BASE_URL=https://qa.example.com
ADMIN_USER=admin_user
ADMIN_PASSWORD=********
EMAIL_RECIPIENTS=team@example.com
```

**Never commit .env.** Add it to .gitignore and share a .env.example with placeholder values instead.

## 2.8 `pytest.ini`: Pytest Settings

**Purpose:** Project-level pytest configuration.

- **Retry** settings for flaky tests (e.g. via pytest-rerunfailures)

- **Markers (tags)** registration: smoke, regression, e2e

- Default CLI options, test paths and file-matching patterns

### `[pytest]` Configuration

testpaths = tests python_files = test_*.py addopts = -v --reruns 1 --reruns-delay 2 --html=reports/report.html --self-contained-html markers = smoke: quick sanity checks on critical flows regression: full functional regression suite e2e: end-to-end business flow tests

## 2.9 `reports/`: Execution Output

**Purpose:** Stores everything produced by a run: HTML report, screenshots of failures, logs.

- Reports can be published through **GitHub** (e.g. GitHub Actions artifacts / GitHub Pages)

- **Screenshots** are captured on failure and linked in the report

- Add reports/ to .gitignore for local runs

## 2.10 Automation Control Sheet

**Purpose:** An Excel sheet that controls _what_ gets executed: which tests or suites are enabled (Yes/No), their priority, and the target environment/browser, without touching code.

Suggested columns: Test ID | Test Name | Module | Marker | Run (Y/N) | Priority | Browser | Remarks

## 3. Naming Conventions

|Item|Convention|Example|
|---|---|---|
|App subfolder (in<br>pages/, tests/,<br>test_data/)|lower_snake_case app<br>name|admin/|
|Page object file|pages/<app>/<br><app>_<screen>_page.p<br>y|pages/admin/<br>admin_access_management_page.py|
|Page object class|PascalCase + Page|AdminAccessManagementPage|
|Test file|tests/<app>/<br>test_<app>_<screen>[_<<br>feature>].py|tests/admin/<br>test_admin_access_management_user.py|
|Test function|test_<action>_<expecte<br>d_result>|test_admin_can_search_user|
|Test data file|test_data/<app>/<br><app>_<screen>_test_d<br>ata.py|test_data/admin/<br>admin_access_management_test_data.py|
|Locator constants|UPPER_SNAKE_CASE|ADD_USER_BUTTON|
|Methods / functions|lower_snake_case, verb<br>first|click_add_user()|
|Markers|lowercase single word|smoke, regression, e2e|

**Important:** pytest discovers files matching test_*.py by default (lowercase). If you prefer the Test_Appname_Screenname.py style, add python_files = Test_*.py test_*.py to pytest.ini. Using lowercase with underscores is recommended since it works on both Windows and Linux CI without surprises.

## 4. Markers (Tags)

Every test case must carry at least one marker so suites can be selected at run time.

|Marker|Meaning|When to run|
|---|---|---|
|smoke|Critical-path sanity checks|**Daily**, and on every build deployment|
|regression|Complete functional coverage|**Twice weekly**, and whenever a new build|
|e2e|Full business flows across modules|**On demand**, before each release|
|App Name|Scripts Related to an APP|**On demand**, for each App.|
|pytest -m s<br>pytest -m "<br>pytest tests|moke<br>regression and not e2e"<br>/test_admin_access_management_u|ser.py -m smoke|

## 5. File Header and Comment Standard

Every file in pages/ and tests/ starts with a header:

_""" Author      : <name> Created On  : <dd-mm-yyyy> Modified By : <name> Modified On : <dd-mm-yyyy> Description : <one-line purpose> """_

Then:

- **Add proper and clear comments for each section** (locator groups, method groups, scenario blocks).

- Update **Modified By / Modified On** whenever you change the file.

## 6. Best Practices

### Design

1. **One subfolder per app** in pages/, tests/ and test_data/, using the same app name in all three so files are easy to trace.

2. **Page Object Model:** tests never contain locators; pages never contain assertions about business outcomes.

3. **Inherit from BasePage:** never call raw Playwright APIs from tests.

4. **One responsibility per file:** pages for UI, utils for helpers, tests for scenarios.

5. **Keep tests independent:** each test sets up and cleans up its own data; no test should rely on another test's outcome.

### Locators

6. Prefer stable, user-facing locators: get_by_role, get_by_label, get_by_test_id, then CSS. Avoid long XPath and index-based selectors.

7. Group locators by screen section and comment each group.

8. Never duplicate a locator. Define once in the page object and reuse.

### Waiting and Stability

9. Rely on Playwright's **auto-waiting** ; avoid time.sleep().

10. Use web-first assertions (expect(locator).to_be_visible()) instead of manual checks.

11. Use retries only for genuine flakiness, and investigate the root cause rather than hiding it.

### Data and Configuration

12. No hard-coded URLs, credentials or test data in code. Use .env and test_data/.

13. Never commit secrets. Use CI secrets for pipelines.

14. Prefer pytest.mark.parametrize for data-driven tests.

### Tests

15. Give every test a clear, behaviour-describing name and at least one marker.

16. One logical verification focus per test; keep tests short and readable.

17. Add meaningful assertion messages so failures are self-explanatory.

18. Capture a **screenshot (and optionally a trace/video) on failure** .

### Code Quality

19. Follow PEP 8; use a formatter/linter (black, ruff / flake8).

20. Review all framework changes via pull requests.

21. Keep requirements.txt pinned and updated.

### Execution and Reporting

22. Run smoke on every build, regression nightly, e2e before release.

23. Run in parallel where tests are independent (pytest-xdist).

24. Publish reports from CI and email a summary using utils/email_utils.py.

25. Maintain the **Automation Control Sheet** so execution scope is visible and controlled.

## 7. Getting Started

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install
```

### 3. Configure the environment

```bash
cp .env.example .env
# Then fill in the real values in .env.
```

### 4. Run tests

```bash
pytest -m smoke
pytest -m regression --headed
pytest -n 4  # Parallel execution with pytest-xdist
```

Suggested requirements.txt:

playwright pytest pytest-playwright pytest-html pytest-rerunfailures pytest-xdist python-dotenv openpyxl

## 8. Adding a New Screen: Checklist

- ☐ Create the app subfolder under pages/, tests/ and test_data/ if it does not exist yet

- ☐ Create pages/<app>/<app>_<screen>_page.py with header, commented locators and methods

- ☐ Add test data in test_data/<app>/<app>_<screen>_test_data.py (or JSON/CSV/Excel)

- ☐ Create tests/<app>/test_<app>_<screen>.py with header, scenario comment and marked test cases

- ☐ Add any new shared helpers to utils/ (only if screen-independent)

- ☐ Register new markers in pytest.ini if required

- ☐ Add the new tests to the Automation Control Sheet

- ☐ Raise a pull request for review
