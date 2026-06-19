import os
import pytest
from playwright.sync_api import sync_playwright
from pages.base_page import BasePage
from pages.login_page import LoginPage
from utils.config import Config


def pytest_addoption(parser):
#    parser.addoption("--browser", action="store", default="chromium")
    parser.addoption("--env", action="store", default="qa")

def pytest_configure(config):
    env = config.getoption("--env")
    os.environ["ENV"] = env

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="function")
def page(request):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        

        base = BasePage(page, Config.get_url())
        base.open_application()

        if "login" in request.keywords:
            login_page = LoginPage(page, Config.get_url())
            login_page.login_user(Config.get_username(), Config.get_password())

        yield page

        if request.node.rep_call.failed:
            base.attach_screenshot("Failure Screenshot")

        context.close()
        browser.close()