# Author : Gowthami Ankem
# Created Date : 2026-11-24

"""
==============  INTRODUCTION ================
Test Module: test_ListView_DepartedSection_DatePicker
Description: Test script to validate Date Picker and Historical Flights in the Departed
             Section of Flights List View.
             - Reads current date.
             - Navigates to a previous historical date using the date picker popup.
             - Verifies that historical departed flights load accurately.
             - Restores back to the current date to keep the dashboard state clean.
"""

import pytest
import allure
from pages.List_View.ListView_Departed_DatePicker_Page import (
    ListView_Departed_DatePicker_Page
)
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_DepartedSection_DatePicker(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation of Date Picker & Historical Departed Flights.

    Steps:
    1. Authenticate / Login to application (managed via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed Section tab.
    4. Select a previous historical date via the date picker.
    5. Verify historical flights load properly.
    6. Restore back to today's date.
    """
    logger.info("Starting Departed Section Date Picker Test")

    datepicker_page = ListView_Departed_DatePicker_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        datepicker_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Section"):
        datepicker_page.select_departed_flights()

    with allure.step("Step 3: Test Date Picker Navigation and Historical Departed Flights"):
        datepicker_page.validate_historical_date_workflow()

    logger.info("Departed Section Date Picker Test completed successfully")
