# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

import pytest
import allure
from pages.List_View.ListView_Ongoing_Lock_Unlock_Flight_Page import (
    List_View_Ongoing_Lock_Unlock_Flight_Page,
)
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_List_View_Ongoing_Lock_Unlock_Flight(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify lock and unlock process (First Lock -> Then Unlock) for an ongoing flight.

    Steps:
      1. Prerequisite: Sign into application using common login method.
      2. Step 1: Navigate to Flights List View dashboard.
      3. Step 2: Make sure Ongoing flights section is loaded.
      4. Step 3: Locate target flight card and ensure it starts in an unlocked state.
      5. Step 4: Lock the flight by entering reason and remarks.
      6. Step 5: Verify that the flight card is now in LOCKED state.
      7. Step 6: Unlock the flight by entering remarks.
      8. Step 7: Verify that the flight card returns to UNLOCKED state.
    """
    logger.info("=== Starting Test: Ongoing Section Sequential Lock & Unlock Flight ===")

    # Prerequisite: Sign into the application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    # Initialize page object
    lock_page = List_View_Ongoing_Lock_Unlock_Flight_Page(page)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            lock_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Make sure the 'Ongoing' section tab is active and flights are visible
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Ongoing Flights Section is Loaded"):
        total_flights = lock_page.ensure_ongoing_section()
        with allure.step(f"2.1: Check Ongoing section tab is active with flight cards loaded (Found: {total_flights} flights)"):
            assert total_flights > 0, "No flights available in Ongoing section."
        allure.attach(
            f"Active Section: Ongoing\nTotal Flight Cards Loaded: {total_flights}",
            name="Ongoing_Section_Status",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Ongoing section active with {total_flights} flight cards.")

    # -------------------------------------------------------------------------
    # Step 3: Find a flight card and ensure it starts in an unlocked state
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Locate Target Flight Card and Ensure Clean Unlocked State"):
        target_flight = lock_page.get_first_flight_card()
        flight_number = lock_page.get_flight_number(target_flight)
        logger.info(f"Selected flight for test: '{flight_number}' in Ongoing section")

        with allure.step(f"3.1: Identify target flight on screen -> Flight Number: '{flight_number}'"):
            assert flight_number, "Failed to retrieve flight number from target card."

        with allure.step(f"3.2: Check if Flight '{flight_number}' is already locked"):
            is_initially_locked = lock_page.is_flight_locked(target_flight)

        # If the flight is already locked from a previous run, unlock it first
        if is_initially_locked:
            with allure.step(f"3.3: Flight '{flight_number}' is initially LOCKED. Resetting to UNLOCKED state first"):
                logger.info(f"Flight '{flight_number}' is initially LOCKED. Resetting to UNLOCKED state first...")
                lock_page.unlock_flight(flight_card=target_flight, remarks="Resetting to unlocked state")
                is_reset = lock_page.wait_for_lock_state(flight_card=target_flight, expected_locked=False, timeout_ms=10000)
                assert is_reset, f"Failed to reset flight '{flight_number}' to unlocked state."

        allure.attach(
            f"Target Flight: {flight_number}\nSection: Ongoing\nInitial Lock State: UNLOCKED (Clean starting state)",
            name=f"{flight_number}_Initial_State",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 4: Lock the flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 4: Lock Flight '{flight_number}' via Ellipsis Menu"):
        logger.info(f"Proceeding to LOCK Flight '{flight_number}'...")
        lock_reason = "Test"
        lock_remarks = "Testing Flight"

        with allure.step(f"4.1: Click ellipsis menu on card, choose 'Lock Flight', and enter Reason: '{lock_reason}', Remarks: '{lock_remarks}'"):
            lock_result = lock_page.lock_flight(
                flight_card=target_flight,
                reason=lock_reason,
                remarks=lock_remarks
            )

        with allure.step(f"4.2: Verify lock submission response values"):
            assert lock_result["flight_number"], "Flight number could not be determined."
            assert lock_result["reason"] == lock_reason, f"Reason did not match expected value '{lock_reason}'."
            assert lock_result["remarks"] == lock_remarks, f"Remarks did not match expected value '{lock_remarks}'."

        allure.attach(
            f"Target Flight: {flight_number}\n"
            f"Action: Lock Flight\n"
            f"Selected Reason: {lock_reason}\n"
            f"Entered Remarks: {lock_remarks}\n"
            f"Status: Lock form submitted successfully.",
            name=f"{flight_number}_Lock_Submission",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 5: Verify that the flight is now LOCKED
    # -------------------------------------------------------------------------
    with allure.step(f"Step 5: Verify and Assert Flight '{flight_number}' is in LOCKED State"):
        target_flight = lock_page.get_first_flight_card()

        with allure.step(f"5.1: Wait for locked state icon to appear on flight card (up to 10s)"):
            is_locked_ok = lock_page.wait_for_lock_state(
                flight_card=target_flight,
                expected_locked=True,
                timeout_ms=10000
            )

        with allure.step(f"5.2: Assert that flight card displays locked status"):
            assert is_locked_ok, (
                f"Post-condition failed: Flight '{flight_number}' is NOT locked after locking action."
            )

        allure.attach(
            f"Flight: {flight_number}\nVerified Lock State: LOCKED\nVerification: Lock icon is visible on card.",
            name=f"{flight_number}_Locked_Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully LOCKED.")

    # -------------------------------------------------------------------------
    # Step 6: Unlock the flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 6: Unlock Flight '{flight_number}' via Lock Icon"):
        logger.info(f"Proceeding to UNLOCK Flight '{flight_number}'...")
        target_flight = lock_page.get_first_flight_card()
        unlock_remarks = "Testing Unlock"

        with allure.step(f"6.1: Click lock icon on flight card and enter unlock Remarks: '{unlock_remarks}'"):
            unlock_result = lock_page.unlock_flight(
                flight_card=target_flight,
                remarks=unlock_remarks
            )

        with allure.step("6.2: Verify unlock dialog submission values"):
            assert unlock_result["remarks"] == unlock_remarks, (
                f"Remarks did not match expected value '{unlock_remarks}'."
            )

        allure.attach(
            f"Target Flight: {flight_number}\n"
            f"Action: Unlock Flight\n"
            f"Entered Remarks: {unlock_remarks}\n"
            f"Status: Unlock form submitted successfully.",
            name=f"{flight_number}_Unlock_Submission",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 7: Verify that the flight is now UNLOCKED
    # -------------------------------------------------------------------------
    with allure.step(f"Step 7: Verify and Assert Flight '{flight_number}' Returns to UNLOCKED State"):
        target_flight = lock_page.get_first_flight_card()

        with allure.step("7.1: Wait for lock icon to detach from flight card (up to 10s)"):
            is_unlocked_ok = lock_page.wait_for_lock_state(
                flight_card=target_flight,
                expected_locked=False,
                timeout_ms=10000
            )

        with allure.step("7.2: Assert that flight card returns to unlocked state"):
            assert is_unlocked_ok, (
                f"Post-condition failed: Flight '{flight_number}' is STILL locked after unlocking."
            )

        allure.attach(
            f"Flight: {flight_number}\nVerified Lock State: UNLOCKED\nVerification: Lock icon is no longer present.",
            name=f"{flight_number}_Unlocked_Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully UNLOCKED.")

    logger.info("=== Completed Test: Ongoing Section Sequential Lock & Unlock Flight successfully ===")
