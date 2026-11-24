# Author : Tilak Badsheshi
# Created Date : 2026-10-26
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

import pytest
import allure
from pages.List_View.ListView_Departed_AccesstoAIMedia import Listview_DepartedSection_AccesstoAIMedia
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_Listview_DepartedSection_AccesstoAIMedia(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify access to AI Media and video playback for departed flights in the Departed section.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Switch to Departed flights section tab.
    4. Step 3: Expand turnaround and split flight activity dropdowns and open AI Media popup player.
    """
    logger.info("Starting List View Departed Section Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    departed_page = Listview_DepartedSection_AccesstoAIMedia(page)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            departed_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Switch to Departed section tab
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Select Departed Flights Section"):
        with allure.step("2.1: Click 'Departed' section tab and check visible flights"):
            departed_page.select_departed_flights()
        allure.attach(
            "Switched to Departed Flights section successfully.",
            name="Departed_Section_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 3: Validate AI Media across departed flights
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Validate All Departed Flights and AI Media"):
        with allure.step("3.1: Expand turnaround and split flight activity dropdowns and open AI media player"):
            departed_page.check_all_departed_flights()
        allure.attach(
            "Validated turnaround flight activities and AI media player popups across departed flights.",
            name="Departed_AIMedia_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.info("List View Departed Section Test completed successfully")
