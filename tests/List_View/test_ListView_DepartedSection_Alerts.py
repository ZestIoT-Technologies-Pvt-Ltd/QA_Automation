# Author : Gowthami Ankem
# Created Date : 2026-11-18

"""
==============  INTRODUCTION ================
Test Module: test_ListView_DepartedSection_Alerts
Description: Test script to validate Alerts in Departed Section of Flights List View.
             Works across SALZBURG, BELFAST, and FLYDUBAI projects.
             Checks departed flight cards for alerts button (.Departed_alerts_buttonOne):
             1. Opens the alerts popup drawer for every flight (including '00'):
                - If count is '00': Verifies empty state ('No alerts found') and reports if alerts are present but count is not showing.
                - If count > 0: Inspects alerts directly, and cycles through 'Critical' and 'Pending' categories.
             2. For each alert card:
                - Opens detail view and switches to History tab.
                - Verifies history timeline rules:
                  * 'Open': Contains 'Alert Generated'
                  * 'Acknowledged': Contains 'Alert Generated' and 'Acknowledged'
                  * 'Closed': Contains 'Alert Generated', 'Acknowledged', and 'Closed'
                - Navigates back to the alert list.
             3. Closes the popup drawer via 'X' to proceed to the next flight.
"""

import pytest
import allure
from pages.List_View.ListView_DepartedSection_Alerts_Page import ListView_DepartedSection_Alerts_Page
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_DepartedSection_Alerts(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation of Alerts in Departed Section.

    Steps:
    1. Authenticate / Login to application (managed as prerequisite via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed Section tab.
    4. Iterate through Departed flight cards:
       - Check if the flight has alerts (alert count > 0).
       - If no alerts, skip the flight.
       - If alerts are present:
         a) Click on the alerts button to open the notifications popup drawer.
         b) For each alert card in the popup:
            - Check alert status:
              * 'Open': Verify timeline history contains 'Alert Generated'.
              * 'Acknowledged': Verify timeline history contains 'Alert Generated' and 'Acknowledged'.
              * 'Closed': Verify timeline history contains 'Alert Generated', 'Acknowledged', and 'Closed'.
            - Navigate back to the alert list.
         c) Close the alerts popup drawer.
    """
    logger.info("Starting Departed Section Alerts Validation Test")

    alerts_page = ListView_DepartedSection_Alerts_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        alerts_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Section"):
        alerts_page.select_departed_flights()

    with allure.step("Step 3: Validate Alerts for Departed Flights"):
        alerts_page.validate_departed_flights_alerts()

    logger.info("Departed Section Alerts Validation Test completed successfully")
