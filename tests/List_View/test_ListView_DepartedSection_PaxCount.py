# Author : Gowthami Ankem
# Created Date : 2026-11-24

"""
==============  INTRODUCTION ================
Test Module: test_ListView_DepartedSection_PaxCount
Description: Test script to validate Passenger (PAX) Count and Segregation Breakdown
             in the Departed Section of Flights List View.
             - Reads Arrival and Departure PAX counts from each departed flight card.
             - Hovers over the PAX column to trigger the segregation popup.
             - Verifies class segregation (J, Y, Infant) and compares calculated totals
               with the flight card values.
"""

import pytest
import allure
from pages.List_View.ListView_DepartedSection_PaxCount_Page import (
    ListView_DepartedSection_PaxCount_Page
)
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_DepartedSection_PaxCount(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation of Departed Flights PAX Count & Breakdown Popup.

    Steps:
    1. Authenticate / Login to application (managed via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed Section tab.
    4. Iterate through Departed flight cards:
       a) Read Arrival & Departure PAX numbers from card.
       b) Hover to open PAX breakdown popup.
       c) Cross-check class totals (J + Y) against card counts.
       d) Dismiss popup and proceed to next flight.
    """
    logger.info("Starting Departed Section PAX Count Validation Test")

    pax_page = ListView_DepartedSection_PaxCount_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        pax_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Section"):
        pax_page.select_departed_flights()

    with allure.step("Step 3: Validate PAX Count Breakdown for Departed Flights"):
        pax_page.validate_departed_pax_counts()

    logger.info("Departed Section PAX Count Validation Test completed successfully")
