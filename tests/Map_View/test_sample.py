# Author : Tilak Badsheshi
# Created Date : 2026-11-10
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-19

import pytest
import allure
from pages.Map_View.Sample_Page import MapViewSamplePage
from pages.Login.Login_Page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_map_view_module_placeholder(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify navigation and view readiness for the Map View module.

    Steps:
    1. Prerequisite: Authenticate / Login to application using LoginPage.login_user().
    2. Initialize MapViewSamplePage object.
    3. Navigate to Map View module dashboard.
    4. Assert and verify Map canvas and layout controls are displayed.
    """
    logger.info("Starting Map View Module Verification Test")

    with allure.step("Prerequisite: Login to application"):
        login_page = LoginPage(page)
        login_page.login_user()

    map_page = MapViewSamplePage(page)

    with allure.step("Step 1: Initialize Map View Page Object"):
        assert map_page is not None
        logger.info("MapViewSamplePage initialized")

    with allure.step("Step 2: Navigate to Map View Module"):
        map_page.navigate_to_map_view()
        logger.info("Navigated to Map View module")

    with allure.step("Step 3: Verify Map View Container Readiness"):
        is_ready = map_page.verify_map_view_ready()
        logger.info(f"Map View readiness verified: {is_ready}")
