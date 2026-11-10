
# Author : Gowthami
# Created Date : 2026-10-26
# Modified By : Gowthami
# Modified Date : 2026-11-10

import pytest
import allure

from pages.List_View.Listview_DepartedSection_AccesstoAIMedia import Listview_DepartedSection_AccesstoAIMedia
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_Listview_DepartedSection_AccesstoAIMedia(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify accessibility and playback of AI Media across departed flights in the Departed section.

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View.
    3. Switch to Departed Flights section.
    4. Validate all departed flights, expand turnaround and split flight accordions, and access AI Media popup player.
    """
    logger.info("Starting List View Departed Section Test")

    departed_page = Listview_DepartedSection_AccesstoAIMedia(page)

    with allure.step("Step 1: Navigate to Flights List View"):
        departed_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Flights Section"):
        departed_page.select_departed_flights()

    with allure.step("Step 3: Validate All Departed Flights and AI Media"):
        departed_page.check_all_departed_flights()

    logger.info("List View Departed Section Test completed successfully")