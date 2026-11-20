# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-19

import pytest
import allure
from pages.Login.Login_Page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_login(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify successful authentication and application launch for AviLeap.

    Steps:
    1. Authenticate / Login to application using LoginPage.login_user().
    2. Retrieve the web page title.
    3. Assert and verify that the page title contains 'AviLeap'.
    """
    logger.info("Starting test_login")

    try:
        login_page = LoginPage(page)

        with allure.step("Step 1: Authenticate / Login to Application"):
            login_page.login_user()

        with allure.step("Step 2: Retrieve Page Title"):
            title = login_page.get_page_title()
            logger.info(f"Page title is: {title}")

        with allure.step("Step 3: Verify Application Title contains 'AviLeap'"):
            assert "AviLeap" in title, f"Expected 'AviLeap' in title, but got '{title}'"
            logger.info("Application title verified successfully")

    except Exception as e:
        logger.error(f"Test failed due to: {str(e)}")
        raise  # VERY IMPORTANT → don’t remove this

    finally:
        logger.info("Test execution completed")