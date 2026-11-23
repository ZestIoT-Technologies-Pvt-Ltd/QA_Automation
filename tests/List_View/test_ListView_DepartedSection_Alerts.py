# Author : Gowthami Ankem
# Created Date : 2026-11-18

"""
==============  INTRODUCTION ================
Test Module: test_ListView_DepartedSection_Alerts
Description: Test script to validate alerts in the Departed section of Flights List View.
             Works across SALZBURG, BELFAST, and FLYDUBAI projects.

Workflow:
1. Open Flights List View and click on the Departed tab.
2. Check the alerts button on each departed flight card:
   - If count is '00': verify the popup opens and confirms 'No alerts found'.
   - If count is greater than 0: inspect active alerts under Critical and Pending categories.
3. For each alert card:
   - Open its detail view.
   - Check Details tab: confirm alert message is shown, and if Critical, verify Criticality is 'Critical'.
   - Check History tab: verify status timeline matches ('Open', 'Acknowledged', 'Closed').
   - Return back to the alert list.
4. Close the alerts popup and proceed to the next flight.
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
    Test Scenario: Validation of Departed Flights Alerts and Status History.

    Steps:
    1. Log in to the application and open Flights List View dashboard.
    2. Select the Departed section tab.
    3. Check alert details (message & criticality) and status history in the popup.
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
