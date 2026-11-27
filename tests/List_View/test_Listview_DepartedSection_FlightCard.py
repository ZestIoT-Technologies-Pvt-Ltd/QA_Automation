# Author : Gowthami Ankem
# Created Date : 2026-11-20

"""
==============  INTRODUCTION ================
Test Module: test_ListView_DepartedSection_FlightCard
Description: Test script to validate Flight Card popup reports in Departed Section of Flights List View.
             Opens the Flight Card report popup (.rh-form) for departed flights and cross-verifies
             that critical flight data—including Flight Number, STA, STD, ETA, ETD, Bay, and Gate—
             matches the flight information displayed on the List View card.
"""

import pytest
import allure
from pages.List_View.ListView_Departed_FlightCard_Page import ListView_Departed_FlightCard_Page
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_DepartedSection_FlightCard(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation and Cross-Verification of Flight Card Data in Departed Section.

    Steps:
    1. Authenticate / Login to application (managed as prerequisite via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed Section tab.
    4. Iterate through Departed flight cards:
       a) Extract flight details from List View card (Flight Number, STA, STD, ETA, ETD, Bay, Gate).
       b) Click the flight's three-dot menu ('more_vert') and select 'Flight Card'.
       c) Switch to the opened Flight Card popup tab (.rh-form).
       d) Cross-verify that extracted List View data matches the data rendered inside the Flight Card:
          - Confirms Flight Number exists on the Flight Card.
          - Confirms STA, STD, ETA, ETD, Bay, and Gate match.
       e) Capture screenshot of the verified Flight Card.
       f) Close the popup tab and proceed to subsequent flights.
    """
    logger.info("Starting Departed Section Flight Card Validation Test")

    flight_card_page = ListView_Departed_FlightCard_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        flight_card_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Section"):
        flight_card_page.select_departed_flights()

    with allure.step("Step 3: Validate Flight Cards and Cross-Verify Data for Departed Flights"):
        flight_card_page.validate_departed_flight_cards()

    logger.info("Departed Section Flight Card Validation Test completed successfully")
