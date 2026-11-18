import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from playwright.sync_api import sync_playwright
from pages.Common_Base_Page.Base_Page import BasePage
from pages.Login.Login_Page import LoginPage
from utils.config import Config
from utils.email_sender import EmailSender

pytest_plugins = ["utils.html_report", "utils.station_config"]


def pytest_addoption(parser):
    existing = set()
    for opt in getattr(parser._anonymous, 'options', []):
        existing.update(opt.names())
    for grp in getattr(parser, '_groups', []):
        for opt in getattr(grp, 'options', []):
            existing.update(opt.names())

    if "--project" not in existing:
        parser.addoption("--project", action="store", default=None, help="Project Name")
    if "--env" not in existing:
        parser.addoption("--env", action="store", default=None, help="Environment Name")
    if "--station" not in existing:
        parser.addoption("--station", action="store", default=None, help="Station Code from Excel config")
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
def station(request):
    """Return the station code for the current test run or test parametrization."""
    if hasattr(request, "param"):
        return request.param
    station_opt = request.config.getoption("--station", default=None)
    if station_opt:
        return [s.strip().upper() for s in str(station_opt).split(",") if s.strip()][0]
    return "DXB"


@pytest.fixture(scope="function")
def page(request, station):

    station_map = getattr(request.config, "framework_station_to_project", {})
    st_info = station_map.get(station, {})
    project = st_info.get("project") or request.config.getoption("--project") or "flydubai"
    env = st_info.get("env") or request.config.getoption("--env") or "qa"
    browser_name = request.config.getoption("--browser") or "chromium"
    headless = getattr(request.config.option, "headless", False)

    config = Config.get_config(project, env)

    with sync_playwright() as p:

        if browser_name.lower() == "chromium":
            args = ["--start-maximized"] if not headless else []
            browser = p.chromium.launch(headless=headless, args=args)

        elif browser_name.lower() == "firefox":
            browser = p.firefox.launch(headless=headless)

        elif browser_name.lower() == "webkit":
            browser = p.webkit.launch(headless=headless)

        else:
            raise ValueError(f"Unsupported browser: {browser_name}")

        context = browser.new_context(
            no_viewport=True
        )

        page = context.new_page()
        request.node._framework_page = page

        base = BasePage(page, config["url"])

        base.open_application()

        if "login" in request.keywords:

            login_page = LoginPage(page, config["url"])

            login_page.login_user(config["username"], config["password"])

        yield page

        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            if not getattr(request.node, "_failure_screenshot_captured", False):
                err = getattr(request.node.rep_call, "longreprtext", "") or ""
                base.capture_failure_screenshot(flight_name=request.node.name, error_message=err)
                setattr(request.node, "_failure_screenshot_captured", True)

        context.close()
        browser.close()


def pytest_sessionstart(session):
    import glob
    os.makedirs("reports", exist_ok=True)
    results_xml = os.path.join("reports", "results.xml")

    if os.path.exists(results_xml):
        os.remove(results_xml)

    # Clean up stale station reports from previous runs so old executions don't linger
    for old_report in glob.glob(os.path.join("reports", "*_Report.html")):
        try:
            os.remove(old_report)
        except Exception:
            pass
    for old_file in (
        os.path.join("reports", "Extent_Report.html"),
        os.path.join("reports", "latest_report.html"),
    ):
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
            except Exception:
                pass


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):

    if getattr(session.config.option, "collectonly", False):
        return

    if session.config.getoption("--no-email", default=False):
        return

    # If html_report plugin already handled email delivery, avoid sending duplicate email
    if getattr(session.config, "_email_delivered", False):
        return

    project = session.config.getoption("--project") or getattr(session.config, "framework_project", None)
    env = session.config.getoption("--env") or getattr(session.config, "framework_env", "qa")
    browser = session.config.getoption("--browser")
    default_st, _ = EmailSender.get_excel_station_config(project)
    station = session.config.getoption("--station", default=default_st)

    try:
        raw_requested = getattr(session.config, "framework_stations_requested", [])
        if not raw_requested and station:
            raw_requested = [s.strip().upper() for s in str(station).split(",") if s.strip()]
        requested_stations = [
            s for s in raw_requested
            if s and s not in ("-", "DEFAULT", "UNKNOWN", "NONE")
        ] or [default_st]

        station_reports = getattr(session.config, "_station_reports", {})
        if not station_reports:
            station_reports = {}
            for st in requested_stations:
                candidate = os.path.join("reports", f"{st}_Report.html")
                if os.path.exists(candidate):
                    station_reports[st] = candidate

        primary_station = requested_stations[0] if requested_stations else default_st
        report_path = station_reports.get(primary_station)
        if not report_path or not os.path.exists(report_path):
            for candidate in [
                os.path.join("reports", f"{primary_station}_Report.html"),
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
            report_paths=station_reports if station_reports else None,
            report_path=None if station_reports else report_path,
        )
        session.config._email_delivered = True

    except Exception as e:
        print(f"Failed to send execution email: {e}")
