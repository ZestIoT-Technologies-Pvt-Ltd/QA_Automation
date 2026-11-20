# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-04

import pytest
import allure
from pages.Login.Login_Page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_login(page):
    """Verifies that the user successfully logs in and arrives at the AviLeap dashboard.

    In simple terms:
    Before this test begins, the browser automatically opens and performs the login
    as a prerequisite (configured in conftest.py).
    This test then checks that the page title contains 'AviLeap', confirming that
    the user is properly authenticated and viewing the application dashboard.
    """
    logger.info("Starting test_login")

    try:
        # Step 1: Connect to the open login page
        login_page = LoginPage(page, None)

        # Step 2: Read the title of the web page currently displayed
        title = login_page.get_page_title()
        logger.info(f"Page title is: {title}")

        # Step 3: Confirm that 'AviLeap' is in the page title
        assert "AviLeap" in title, f"Expected 'AviLeap' in page title, but got '{title}'"

    except Exception as e:
        logger.error(f"Test failed due to: {str(e)}")
        raise  # Re-raise error so the test is marked as failed and report captures it

    finally:
        logger.info("Test execution completed")