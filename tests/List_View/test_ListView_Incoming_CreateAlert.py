# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

import pytest
import allure
from pages.List_View.ListView_Incoming_Create_Alert_Page import ListView_Incoming_Create_Alert_Page
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_ListView_Incoming_CreateAlert(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify whether a flight-level alert can be created against a flight in Flights List View (Incoming section).

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View.
    3. Ensure Incoming Section is active.
    4. Select an eligible flight card with an available action menu.
    5. Record the initial alert count from the flight card.
    6. Click the Three-Dots menu ('more_vert') on the flight card.
    7. Select 'Add Alert/Task' from the menu.
    8. In the Add Alert/Task popup:
       - Enter Task Name as 'Test Alert' (based on category 'Alert').
       - Select Alert Category as 'Alert' from the PrimeNG dropdown.
       - Select Alert Type toggle as 'Arrival'.
       - Click 'Save' button to create the alert.
    9. Refresh the Incoming page using the Refresh icon ('Refresh Flight' / 'pi-sync') on the List View:
       - After refreshing, the system loading spinner will be displayed.
       - Wait for the loading spinner to complete.
       - Verify that the alert count has updated / increased for the flight.
    10. Click on the Alert count column of the same flight to open the right-side Alert Details popup.
    11. Verify whether the created alert ('Test Alert') is displayed in the right popup:
        - If displayed -> Test PASSED.
        - If not displayed -> Test FAILED.
    12. Close the right-side Alert Details popup.
    """
    logger.info("=== Starting Test: Create Flight-Level Alert in Incoming Section ===")

    alert_page = ListView_Incoming_Create_Alert_Page(page)

    with allure.step("Step 1: Navigate to Flights List View"):
        alert_page.navigate_to_list_view_page()

    with allure.step("Step 2: Ensure Incoming Section is Active"):
        total_flights = alert_page.ensure_incoming_section()
        assert total_flights > 0, "No flights available in Incoming section."
        logger.info(f"Incoming section active with {total_flights} flight cards.")

    with allure.step("Step 3: Select Eligible Flight Card"):
        target_flight = alert_page.get_flight_card_with_actions_menu()
        flight_number = alert_page.get_flight_number(target_flight)
        initial_count = alert_page.get_alert_count(target_flight)
        logger.info(f"Target Incoming Flight: '{flight_number}' | Initial Alert Count: '{initial_count}'")

    with allure.step(f"Step 4: Create Flight-Level Alert for Flight '{flight_number}'"):
        creation_data = alert_page.create_flight_alert(
            flight_card=target_flight,
            category="Alert",
            task_name="Test Alert",
            alert_type="Arrival",
        )
        assert creation_data["task_name"] == "Test Alert", "Task name does not match 'Test Alert'."
        assert creation_data["category"] == "Alert", "Alert category does not match 'Alert'."
        assert creation_data["alert_type"] in ("Departure", "Turnaround", "Arrival"), f"Alert type unexpected: {creation_data['alert_type']}"
        logger.info(f"Alert form submitted successfully for '{flight_number}': {creation_data}")

    with allure.step("Step 5: Verify Fallback Success Message is Displayed in System"):
        assert creation_data["is_success"], (
            "FAILED: Fallback success message (e.g. 'Alert raised successfully') was NOT displayed "
            f"after submitting alert for flight '{flight_number}'."
        )
        logger.info(
            f"PASSED: Fallback success message '{creation_data['success_message']}' displayed in system!"
        )

    with allure.step(f"Step 6: Refresh Incoming Flights via Refresh Icon & Check Alert Count"):
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

    with allure.step(f"Step 7: Open Right-Side Alert Details Popup by Clicking Alert Column"):
        alert_page.open_alert_details_popup(updated_card)

    with allure.step("Step 8: Verify Alert 'Test Alert' is Displayed in Right Popup"):
        is_displayed = alert_page.is_alert_displayed_in_popup(
            expected_task_name="Test Alert",
            timeout_sec=30,
        )
        assert is_displayed, (
            f"FAILED: Alert 'Test Alert' was NOT displayed in the right-side Alert Details popup "
            f"for flight '{flight_number}'."
        )
        logger.info(f"PASSED: Alert 'Test Alert' is displayed in right popup for flight '{flight_number}'!")

    with allure.step("Step 9: Close Right-Side Alert Details Popup"):
        alert_page.close_alert_details_popup()

    logger.info("=== Completed Test: Create Flight-Level Alert in Incoming Section successfully ===")
