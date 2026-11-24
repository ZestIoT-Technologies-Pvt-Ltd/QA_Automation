# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-23

import pytest
import allure
from pages.List_View.ListView_Ongoing_Create_Alert_Page import List_View_Create_Alert_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_List_View_Create_Alert(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify creating and validating a flight-level alert in the Ongoing section.

    Steps:
      1. Prerequisite: Authenticate / Login to application using common login method.
      2. Step 1: Navigate to Flights List View screen.
      3. Step 2: Ensure Ongoing flights section is active and flight cards are loaded.
      4. Step 3: Select flight card with actions menu and record initial alert count.
      5. Step 4: Open form and create flight-level alert ('Test Alert' under 'Alert' category).
      6. Step 5: Verify confirmation / fallback success message is displayed.
      7. Step 6: Refresh ongoing flights list and verify alert count increases by 1.
      8. Step 7: Open right-side Alert Details popup drawer for the flight.
      9. Step 8: Verify created alert 'Test Alert' is displayed in the popup drawer.
     10. Step 9: Close right-side Alert Details popup drawer.
    """
    logger.info("=== Starting Test: Create Flight-Level Alert in Ongoing Section ===")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    # Create an instance of the Ongoing Create Alert page object
    alert_page = List_View_Create_Alert_Page(page)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Screen"):
        with allure.step("1.1: Open main navigation drawer and click 'Flights' menu option"):
            alert_page.navigate_to_list_view_page()
        allure.attach(
            "Navigated successfully to Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Make sure the 'Ongoing' section tab is active
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Ongoing Flights Section is Loaded and Flights are Loaded"):
        total_flights = alert_page.ensure_ongoing_section()
        with allure.step(f"2.1: Verify Ongoing tab is active with flight cards displayed"):
            assert total_flights > 0, "No flights available in Ongoing section."
        allure.attach(
            f"Target Section: Ongoing\nTotal Flight Cards Displayed: {total_flights}",
            name="Ongoing_Section_Overview",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Ongoing section active with {total_flights} flight cards.")

    # -------------------------------------------------------------------------
    # Step 3: Find a flight card that has an available actions menu
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Select Flight Card and Record Initial Alert Count"):
        target_flight = alert_page.get_flight_card_with_actions_menu()
        flight_number = alert_page.get_flight_number(target_flight)
        initial_count = alert_page.get_alert_count(target_flight)

        with allure.step(f"3.1: Select flight card with accessible ellipsis menu"):
            assert flight_number, "Failed to extract flight number from target card."

        with allure.step(f"3.2: Record initial alert count for Flight"):
            pass

        allure.attach(
            f"Target Flight: {flight_number}\nInitial Alert Count: {initial_count}\n"
            f"Selection Criteria: Flight card has an active ellipsis menu and readable flight number.",
            name=f"{flight_number}_Initial_Selection",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Target Ongoing Flight: '{flight_number}' | Initial Alert Count: '{initial_count}'")

    # -------------------------------------------------------------------------
    # Step 4: Open the form and create a new alert for this flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 4: Fill and Submit Alert Form for Flight"):
        with allure.step("4.1: Open Ellipsis Menu, select 'Add Alert/Task', and enter alert parameters"):
            creation_data = alert_page.create_flight_alert(
                flight_card=target_flight,
                category="Alert",
                task_name="Test Alert",
                alert_type="Departure",
            )

        with allure.step("4.2: Validate form submission payload values"):
            assert creation_data["task_name"] == "Test Alert", "Task name does not match 'Test Alert'."
            assert creation_data["category"] == "Alert", "Alert category does not match 'Alert'."
            assert creation_data["alert_type"] in ("Departure", "Turnaround", "Arrival"), (
                f"Alert type unexpected: {creation_data['alert_type']}"
            )

        allure.attach(
            f"Flight Number: {flight_number}\n"
            f"Category: {creation_data.get('category')}\n"
            f"Task Name: {creation_data.get('task_name')}\n"
            f"Alert Type: {creation_data.get('alert_type')}\n"
            f"Form Submission Status: Submitted\n"
            f"System Response: {creation_data.get('success_message', 'Submitted')}",
            name=f"{flight_number}_Alert_Creation_Data",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Alert form submitted successfully for '{flight_number}': {creation_data}")

    # -------------------------------------------------------------------------
    # Step 5: Check that the system displayed a success confirmation popup
    # -------------------------------------------------------------------------
    with allure.step(f"Step 5: Verify Success Confirmation Message for Flight"):
        with allure.step(f"5.1: Assert confirmation message appeared -> '{creation_data['success_message']}'"):
            assert creation_data["is_success"], (
                "FAILED: Fallback success message (e.g. 'Alert raised successfully') was NOT displayed "
                f"after submitting alert for flight '{flight_number}'."
            )
        allure.attach(
            f"Flight Number: {flight_number}\n"
            f"Success Message Displayed: '{creation_data['success_message']}'\n"
            f"Confirmation Status: PASSED",
            name=f"{flight_number}_Success_Confirmation",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(
            f"PASSED: Fallback success message '{creation_data['success_message']}' displayed in system!"
        )

    # -------------------------------------------------------------------------
    # Step 6: Click the Refresh icon and verify the alert number increases by 1
    # -------------------------------------------------------------------------
    with allure.step(f"Step 6: Refresh Ongoing Flights and Verify Alert Count Updates"):
        with allure.step("6.1: Click Refresh Flight sync icon and wait for updated flight card"):
            is_updated, updated_count, updated_card = alert_page.refresh_and_wait_for_alert_count_update(
                flight_number=flight_number,
                initial_count=initial_count,
                flight_card=target_flight,
                initial_wait_sec=4,
                retry_interval_sec=5,
                max_attempts=4,
            )

        with allure.step(f"6.2: Assert Alert Count Updated -> Initial: '{initial_count}' -> Updated: '{updated_count}'"):
            assert is_updated, (
                f"FAILED: Alert count did not increase for flight '{flight_number}' after creating alert "
                f"and refreshing flights list. Initial count: '{initial_count}', Current count: '{updated_count}'"
            )

        allure.attach(
            f"Flight Number: {flight_number}\n"
            f"Initial Alert Count: {initial_count}\n"
            f"Updated Alert Count: {updated_count}\n"
            f"Increment (+1) Verified: True\n"
            f"Status: PASSED",
            name=f"{flight_number}_Alert_Count_Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(
            f"Alert count result for '{flight_number}': is_updated={is_updated}, "
            f"Initial Count='{initial_count}', Updated Count='{updated_count}'"
        )

    # -------------------------------------------------------------------------
    # Step 7: Click on the alert count number to open the right-side details panel
    # -------------------------------------------------------------------------
    with allure.step(f"Step 7: Open Right-Side Alert Details Popup"):
        with allure.step(f"7.1: Click on alert count on flight card"):
            alert_page.open_alert_details_popup(updated_card)
        allure.attach(
            f"Flight Number: {flight_number}\n"
            f"Action: Clicked alert counter badge ({updated_count}) to open the right-side Alert Details drawer.",
            name=f"{flight_number}_Open_Alert_Drawer",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 8: Verify that our created alert appears in the right-side panel
    # -------------------------------------------------------------------------
    with allure.step(f"Step 8: Verify Newly Created Alert 'Test Alert' is Listed for Flight"):
        with allure.step("8.1: Check alert is listed in Alert Details popup for task name 'Test Alert'"):
            is_displayed = alert_page.is_alert_displayed_in_popup(
                expected_task_name="Test Alert",
                timeout_sec=30,
            )

        with allure.step("8.2: Assert that alert 'Test Alert' is visible in Popup"):
            assert is_displayed, (
                f"FAILED: Alert 'Test Alert' was NOT displayed in the right-side Alert Details popup "
                f"for flight '{flight_number}'."
            )

        allure.attach(
            f"Flight Number: {flight_number}\n"
            f"Expected Alert Task Name: 'Test Alert'\n"
            f"Found in Popup Drawer: True\n"
            f"Status: PASSED",
            name=f"{flight_number}_Drawer_Alert_Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"PASSED: Alert 'Test Alert' is displayed in right popup for flight '{flight_number}'!")

    # -------------------------------------------------------------------------
    # Step 9: Close the right-side alert details panel
    # -------------------------------------------------------------------------
    with allure.step(f"Step 9: Close Right-Side Alert Details Popup Drawer for Flight"):
        with allure.step("9.1: Click close button on right-side alert Popup"):
            alert_page.close_alert_details_popup()
        allure.attach(
            f"Flight Number: {flight_number}\n"
            f"Action: Closed Alert Details popup drawer cleanly.",
            name=f"{flight_number}_Close_Drawer",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.info("=== Completed Test: Create Flight-Level Alert in Ongoing Section successfully ===")
