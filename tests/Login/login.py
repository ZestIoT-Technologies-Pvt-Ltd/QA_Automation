# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

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
    1. Authenticate / Login to application (managed via @pytest.mark.login fixture).
    2. Initialize LoginPage object with active browser page context.
    3. Retrieve the web page title.
    4. Assert and verify that the page title contains 'AviLeap'.
    """
    logger.info("Starting test_login")

    try:
        with allure.step("Step 1: Initialize Login Page Object"):
            login_page = LoginPage(page, None)

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