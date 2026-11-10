
# Author : Gowthami
# Created Date : 2026-10-26
# Modified By : Gowthami
# Modified Date : 2026-11-10

import pytest
import allure

from pages.List_View.Listview_DepartedSection_FlightCard import (Listview_DepartedSection_FlightCard)
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_Listview_DepartedSection_FlightCard(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify accessing and validating Flight Cards for departed flights in the Departed section.

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View.
    3. Switch to Departed Flights section.
    4. Validate Flight Cards across all departed flights (opens card via three-dots menu, verifies new window, closes tab).
    """
    logger.info("Starting List View Departed Flight Card Test")

    departed_page = Listview_DepartedSection_FlightCard(page)

    with allure.step("Step 1: Navigate to Flights List View"):
        departed_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Flights Section"):
        departed_page.select_departed_flights()

    with allure.step("Step 3: Validate Flight Cards for all Departed Flights"):
        departed_page.check_all_departed_flight_cards()

    logger.info(
        "List View Departed Flight Card Test completed successfully"
    )