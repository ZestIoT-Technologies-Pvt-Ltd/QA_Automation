import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from playwright.sync_api import sync_playwright
from pages.Common_Base_Page.Base_Page import BasePage
from pages.Login.Login_Page import LoginPage
from utils.config import Config
from utils.email_sender import EmailSender

pytest_plugins = ["utils.html_report"]


def pytest_addoption(parser):
    existing = set()
    for opt in getattr(parser._anonymous, 'options', []):
        existing.update(opt.names())
    for grp in getattr(parser, '_groups', []):
        for opt in getattr(grp, 'options', []):
            existing.update(opt.names())

    if "--project" not in existing:
        parser.addoption("--project", action="store", default="flydubai", help="Project Name")
    if "--env" not in existing:
        parser.addoption("--env", action="store", default="qa", help="Environment Name")
    if "--station" not in existing:
        default_station, _ = EmailSender.get_excel_station_config("flydubai")
        parser.addoption("--station", action="store", default=default_station, help="Station Code from Excel config")
    if "--browser" not in existing:
        parser.addoption("--browser", action="store", default="chromium", help="Browser Name")
    if "--no-email" not in existing:
        parser.addoption("--no-email", action="store_true", default=False, help="Disable report email delivery for this run.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):

    outcome = yield
    rep = outcome.get_result()

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="function")
def page(request):

    project = request.config.getoption("--project")
    env = request.config.getoption("--env")
    browser_name = request.config.getoption("--browser")

    config = Config.get_config(project, env)

    with sync_playwright() as p:

        if browser_name.lower() == "chromium":
            browser = p.chromium.launch(headless=False,args=["--start-maximized"])

        elif browser_name.lower() == "firefox":
            browser = p.firefox.launch(headless=False)

        elif browser_name.lower() == "webkit":
            browser = p.webkit.launch(headless=False)

        else:
            raise ValueError(f"Unsupported browser: {browser_name}")

        context = browser.new_context(
            no_viewport=True
        )

        page = context.new_page()
        request.node._framework_page = page

        base = BasePage(page,config["url"])

        base.open_application()

        if "login" in request.keywords:

            login_page = LoginPage(page,config["url"])

            login_page.login_user(config["username"],config["password"])

        yield page

        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            base.capture_failure_screenshot(flight_name=request.node.name)

        context.close()
        browser.close()


def pytest_sessionstart(session):

    os.makedirs("reports", exist_ok=True)
    results_xml = os.path.join("reports", "results.xml")

    if os.path.exists(results_xml):
        os.remove(results_xml)


def pytest_sessionfinish(session, exitstatus):

    if getattr(session.config.option, "collectonly", False):
        return

    if session.config.getoption("--no-email", default=False):
        return

    # If html_report plugin already handled email delivery, avoid sending duplicate email
    if getattr(session.config, "_email_delivered", False):
        return

    project = session.config.getoption("--project")
    env = session.config.getoption("--env")
    browser = session.config.getoption("--browser")
    default_st, _ = EmailSender.get_excel_station_config(project)
    station = session.config.getoption("--station", default=default_st)

    try:
        report_path = getattr(session.config, "_extent_report_path", None)
        if not report_path or not os.path.exists(report_path):
            for candidate in [
                os.path.join("reports", "Extent_Report.html"),
                os.path.join("reports", "latest_report.html"),
            ]:
                if os.path.exists(candidate):
                    report_path = candidate
                    break

        email = EmailSender()
        email.send_execution_report(
            project=project,
            env=env,
            browser=browser,
            station=station,
            xml_file=os.path.join("reports", "results.xml"),
            report_path=report_path,
        )
        session.config._email_delivered = True

    except Exception as e:
        print(f"Failed to send execution email: {e}")
