# Author : Tilak Badsheshi
# Created Date : 2026-10-26
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

import pytest
import allure
from pages.List_View.ListView_Departed_FlightCard import Listview_DepartedSection_FlightCard
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_Listview_DepartedSection_FlightCard(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify opening and checking Flight Cards for departed flights in the Departed section.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Switch to Departed flights section tab.
    4. Step 3: Open and validate Flight Card in a new tab for departed flights.
    """
    logger.info("Starting List View Departed Flight Card Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    departed_page = Listview_DepartedSection_FlightCard(page)

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
    # Step 3: Validate Flight Cards across departed flights
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Validate Flight Cards for all Departed Flights"):
        with allure.step("3.1: Open ellipsis menu, select Flight Card option, and verify new tab"):
            departed_page.check_all_departed_flight_cards()
        allure.attach(
            "Validated Flight Cards opened in a new tab and closed properly across departed flights.",
            name="Departed_FlightCards_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.info("List View Departed Flight Card Test completed successfully")
