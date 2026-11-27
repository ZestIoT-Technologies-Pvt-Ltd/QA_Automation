# Author : Gowthami Ankem
# Created Date : 2026-11-18

"""
==============  INTRODUCTION ================
Test Module: test_ListView_Departed_DelayCode
Description: Test script to validate Delay Codes in Departed Section of Flights List View.
             Checks departed flight cards for green delay code icons. If green, opens the
             popup, extracts 'Codes Entered' and 'Total Delay Mins', and verifies the count
             and minutes match the delay codes table rows below. If not green, leaves the flight.
"""

import pytest
import allure
from pages.List_View.ListView_Departed_DelayCode_Page import ListView_Departed_DelayCode_Page
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_Departed_DelayCode(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation of Delay Codes in Departed Section.

    Steps:
    1. Authenticate / Login to application (managed as prerequisite via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed Section tab.
    4. Iterate through Departed flight cards:
       - If the Delay Code icon is green:
         a) Click on the green delay code icon to open the Delay Codes popup.
         b) Extract 'Codes Entered' count and 'Total Delay Mins' from summary.
         c) Verify that the count of delay codes listed in the table below matches 'Codes Entered'.
         d) Verify that the sum of delay minutes in the table matches 'Total Delay Mins'.
         e) Close the popup.
       - If the Delay Code icon is NOT green, leave / skip that flight.
    """
    logger.info("Starting Departed Section Delay Code Test")

    delay_code_page = ListView_Departed_DelayCode_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        delay_code_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Section"):
        delay_code_page.select_departed_flights()

    with allure.step("Step 3: Validate Delay Codes for Departed Flights"):
        delay_code_page.validate_departed_delay_codes()

    logger.info("Departed Section Delay Code Test completed successfully")
