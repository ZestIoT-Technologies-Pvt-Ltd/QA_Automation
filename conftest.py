"""Pytest configuration and test setup module.

This file acts as the central control room for our test automation.
It defines shared settings, browser setup and teardown, automatic application login,
and reporting hooks so each test script can run smoothly without repeating boilerplate code.
"""

import os
import pytest
from playwright.sync_api import sync_playwright
from pages.Common_Base_Page.Base_Page import BasePage
from pages.Login.Login_Page import LoginPage
from utils.config import Config
from utils.email_sender import EmailSender

# Load our interactive Extent HTML reporting plugin
pytest_plugins = ["utils.html_report"]


def pytest_addoption(parser):
    """Adds custom command-line options so you can control test runs from the terminal.

    In simple terms:
    When you run 'pytest' in your terminal, this function lets you customize what happens.
    For example, you can choose which project to test, which environment to use, which
    browser to open, and whether to send an email summary.

    Examples:
        pytest --project SALZBURG --env qa
        pytest --browser firefox --no-email
        pytest --station DXB
    """
    existing = set()
    for opt in getattr(parser._anonymous, 'options', []):
        existing.update(opt.names())
    for grp in getattr(parser, '_groups', []):
        for opt in getattr(grp, 'options', []):
            existing.update(opt.names())

    # Which application project to test (defaults to SALZBURG)
    if "--project" not in existing:
        parser.addoption("--project", action="store", default="SALZBURG", help="Project Name (e.g., SALZBURG, FLYDUBAI, BELFAST)")

    # Which environment to run tests against (defaults to qa)
    if "--env" not in existing:
        parser.addoption("--env", action="store", default="qa", help="Environment Name (e.g., qa, dev, staging, prod)")

    # Which browser to run tests on (defaults to Google Chrome / Chromium)
    if "--browser" not in existing:
        parser.addoption("--browser", action="store", default="chromium", help="Browser Name (chromium, firefox, or webkit)")

    # Turn off email sending if you are just testing locally
    if "--no-email" not in existing:
        parser.addoption("--no-email", action="store_true", default=False, help="Disable report email delivery for this run.")

    # Which airport station to validate (defaults to DEL)
    if "--station" not in existing:
        parser.addoption("--station", action="store", default="DEL", help="Airport/Station Code (e.g., DEL, DXB, DWC)")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    """Monitors the test execution status (passed or failed) during each step.

    In simple terms:
    A test has three stages: setup, the actual test steps, and teardown.
    This function checks each stage and saves the result (pass/fail).
    If a failure happens, other parts of our framework (like screenshot capture)
    will immediately know and take action.
    """
    outcome = yield
    rep = outcome.get_result()

    # Save the status on the test item so fixtures can see if the test passed or failed
    setattr(item, "rep_" + rep.when, rep)


def login_to_application(page, config):
    """Logs into the web application using saved credentials.

    In simple terms:
    This function acts as a required first step (prerequisite) for all tests.
    It takes the open browser page, enters the configured username and password,
    and clicks the login button to enter the main dashboard.

    Args:
        page: The active browser window/tab.
        config: A dictionary containing the application URL, username, and password.

    Returns:
        LoginPage: The initialized login page object.
    """
    login_page = LoginPage(page, config["url"])
    login_page.login_user(config["username"], config["password"])
    return login_page


@pytest.fixture(scope="function")
def login(page, request):
    """A reusable helper (fixture) that performs login when requested.

    In simple terms:
    If any test explicitly asks for 'login' as an input parameter, this function
    retrieves the right project credentials and performs the login automatically.
    """
    project = request.config.getoption("--project")
    env = request.config.getoption("--env")
    config = Config.get_config(project, env)
    return login_to_application(page, config)


@pytest.fixture(scope="function")
def page(request):
    """Main browser setup and cleanup fixture for every test script.

    In simple terms, this function does the heavy lifting before and after each test:
    1. Reads your chosen project, environment, and browser settings.
    2. Opens a real browser window on your screen (in full-screen mode).
    3. Navigates to the application website.
    4. Automatically logs in with valid credentials so the test starts on the dashboard.
    5. Hands the browser page to your test script so your test actions can run.
    6. If the test fails, it captures a failure screenshot with the problem element highlighted.
    7. Cleans up and closes the browser window once the test is finished.
    """
    # Step 1: Read configuration options
    project = request.config.getoption("--project")
    env = request.config.getoption("--env")
    browser_name = request.config.getoption("--browser")

    config = Config.get_config(project, env)

    # Step 2: Start the browser engine (Playwright)
    with sync_playwright() as p:

        if browser_name.lower() == "chromium":
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])

        elif browser_name.lower() == "firefox":
            browser = p.firefox.launch(headless=False)

        elif browser_name.lower() == "webkit":
            browser = p.webkit.launch(headless=False)

        else:
            raise ValueError(f"Unsupported browser: {browser_name}")

        # Step 3: Create a fresh browser context and open a new page/tab
        context = browser.new_context(
            no_viewport=True
        )

        page = context.new_page()
        # Save page reference so reporters can capture screenshots on failure
        request.node._framework_page = page

        # Step 4: Open the application website
        base = BasePage(page, config["url"])
        base.open_application()

        # Step 5: Prerequisite - Automatically log in to the application
        login_to_application(page, config)

        # Step 6: Hand the prepared page over to the test function to run its steps
        yield page

        # Step 7: Post-test check - If the test failed, capture a failure screenshot
        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            base.capture_failure_screenshot(flight_name=request.node.name)

        # Step 8: Clean up and close the browser session
        context.close()
        browser.close()


def pytest_sessionstart(session):
    """Prepares the workspace before any tests begin running.

    In simple terms:
    This function runs once before anything else starts.
    It makes sure the 'reports' folder exists on your computer and removes
    any old XML result files from earlier runs so we always start fresh.
    """
    os.makedirs("reports", exist_ok=True)
    results_xml = os.path.join("reports", "results.xml")

    if os.path.exists(results_xml):
        os.remove(results_xml)


def pytest_sessionfinish(session, exitstatus):
    """Final wrap-up hook that runs after all tests have finished.

    In simple terms:
    When all tests are done running, this function marks the end of the session.
    Our reporting tool (utils.html_report) then builds the interactive HTML report,
    attaches failure screenshots, and sends out the summary email.
    """
    pass
