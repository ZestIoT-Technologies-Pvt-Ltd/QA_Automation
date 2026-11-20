# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

import pytest
import allure
from pages.List_View.ListView_Incoming_Create_Alert_Page import ListView_Incoming_Create_Alert_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_ListView_Incoming_CreateAlert(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify creating and validating a flight-level alert in the Incoming section.

    Steps:
      1. Prerequisite: Authenticate / Login to application using common login method.
      2. Navigate to Flights List View screen.
      3. Ensure Incoming flights section is active.
      4. Select eligible flight card and record initial alert count.
      5. Create flight-level alert ('Test Alert' under 'Alert' category).
      6. Verify fallback success message is displayed.
      7. Refresh incoming flights list and verify alert count increases by 1.
      8. Open right-side Alert Details popup for the flight.
      9. Verify created alert is displayed in the popup.
     10. Close right-side Alert Details popup.
    """
    logger.info("=== Starting Test: Create Flight-Level Alert in Incoming Section ===")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    # Create an instance of the Incoming Create Alert page object
    alert_page = ListView_Incoming_Create_Alert_Page(page)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View"):
        # Clicks the main menu and navigates to the Flights screen
        alert_page.navigate_to_list_view_page()

    # -------------------------------------------------------------------------
    # Step 2: Make sure the 'Incoming' section tab is active
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Incoming Section is Active"):
        # Clicks on the 'Incoming' tab and checks that flight cards are displayed on the screen
        total_flights = alert_page.ensure_incoming_section()
        assert total_flights > 0, "No flights available in Incoming section."
        logger.info(f"Incoming section active with {total_flights} flight cards.")

    # -------------------------------------------------------------------------
    # Step 3: Find a flight card that has an available actions menu
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Select Eligible Flight Card"):
        # Selects the first flight card that has an ellipsis (three-dots) menu ready to be clicked
        target_flight = alert_page.get_flight_card_with_actions_menu()
        flight_number = alert_page.get_flight_number(target_flight)
        # Record the starting alert count so we can verify it increases later
        initial_count = alert_page.get_alert_count(target_flight)
        logger.info(f"Target Incoming Flight: '{flight_number}' | Initial Alert Count: '{initial_count}'")

    # -------------------------------------------------------------------------
    # Step 4: Open the form and create a new alert for this flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 4: Create Flight-Level Alert for Flight '{flight_number}'"):
        # Opens the ellipsis menu, clicks 'Add Alert/Task', enters details, and clicks Save
        creation_data = alert_page.create_flight_alert(
            flight_card=target_flight,
            category="Alert",
            task_name="Test Alert",
            alert_type="Arrival",
        )
        # Check that the form entered the exact task name and category we asked for
        assert creation_data["task_name"] == "Test Alert", "Task name does not match 'Test Alert'."
        assert creation_data["category"] == "Alert", "Alert category does not match 'Alert'."
        assert creation_data["alert_type"] in ("Departure", "Turnaround", "Arrival"), f"Alert type unexpected: {creation_data['alert_type']}"
        logger.info(f"Alert form submitted successfully for '{flight_number}': {creation_data}")

    # -------------------------------------------------------------------------
    # Step 5: Check that the system displayed a success confirmation popup
    # -------------------------------------------------------------------------
    with allure.step(f"Step 5: Verify Fallback Success Message is Displayed for Flight '{flight_number}'"):
        assert creation_data["is_success"], (
            "FAILED: Fallback success message (e.g. 'Alert raised successfully') was NOT displayed "
            f"after submitting alert for flight '{flight_number}'."
        )
        logger.info(
            f"PASSED: Fallback success message '{creation_data['success_message']}' displayed in system!"
        )

    # -------------------------------------------------------------------------
    # Step 6: Click the Refresh icon and verify the alert number increases by 1
    # -------------------------------------------------------------------------
    with allure.step(f"Step 6: Refresh Incoming Flights & Check Alert Count for Flight '{flight_number}'"):
        # Clicks the refresh flight icon and waits until the alert count number goes up
        is_updated, updated_count, updated_card = alert_page.refresh_and_wait_for_alert_count_update(
            flight_number=flight_number,
            initial_count=initial_count,
            flight_card=target_flight,
            initial_wait_sec=4,
            retry_interval_sec=5,
            max_attempts=4,
        )
        logger.info(
            f"Alert count result for '{flight_number}': is_updated={is_updated}, "
            f"Initial Count='{initial_count}', Updated Count='{updated_count}'"
        )
        assert is_updated, (
            f"FAILED: Alert count did not increase for flight '{flight_number}' after creating alert "
            f"and refreshing flights list. Initial count: '{initial_count}', Current count: '{updated_count}'"
        )

    # -------------------------------------------------------------------------
    # Step 7: Click on the alert count number to open the right-side details panel
    # -------------------------------------------------------------------------
    with allure.step(f"Step 7: Open Right-Side Alert Details Popup for Flight '{flight_number}'"):
        alert_page.open_alert_details_popup(updated_card)

    # -------------------------------------------------------------------------
    # Step 8: Verify that our created alert appears in the right-side panel
    # -------------------------------------------------------------------------
    with allure.step(f"Step 8: Verify Alert 'Test Alert' is Displayed in Right Popup for Flight '{flight_number}'"):
        is_displayed = alert_page.is_alert_displayed_in_popup(
            expected_task_name="Test Alert",
            timeout_sec=30,
        )
        assert is_displayed, (
            f"FAILED: Alert 'Test Alert' was NOT displayed in the right-side Alert Details popup "
            f"for flight '{flight_number}'."
        )
        logger.info(f"PASSED: Alert 'Test Alert' is displayed in right popup for flight '{flight_number}'!")

    # -------------------------------------------------------------------------
    # Step 9: Close the right-side alert details panel
    # -------------------------------------------------------------------------
    with allure.step(f"Step 9: Close Right-Side Alert Details Popup for Flight '{flight_number}'"):
        alert_page.close_alert_details_popup()

    logger.info("=== Completed Test: Create Flight-Level Alert in Incoming Section successfully ===")
