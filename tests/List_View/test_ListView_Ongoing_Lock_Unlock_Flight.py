# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-19

import pytest
import allure
from pages.List_View.ListView_Ongoing_Lock_Unlock_Flight_Page import (
    List_View_Ongoing_Lock_Unlock_Flight_Page,
)
from pages.Login.Login_Page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_List_View_Ongoing_Lock_Unlock_Flight(page):
    """
        ==============  TEST OVERVIEW ================

    Test Scenario: Verify sequential lock and unlock workflow for an ongoing flight.

    Steps:
      1. Prerequisite: Authenticate / Login to application using LoginPage.login_user().
      2. Navigate to Flights List View screen.
      3. Ensure Ongoing flights section is active.
      4. Locate target flight card and ensure it starts in an unlocked state.
      5. Lock the flight via ellipsis menu with reason and remarks.
      6. Confirm that the flight card displays the locked state icon.
      7. Unlock the flight directly via lock icon with remarks.
      8. Confirm that the flight card returns to the unlocked state.
    """
    logger.info("=== Starting Test: Ongoing Section Sequential Lock & Unlock Flight ===")

    # -------------------------------------------------------------------------
    # Prerequisite: Sign in to the AviLeap application with valid credentials
    # -------------------------------------------------------------------------
    with allure.step("Prerequisite: Login to application"):
        login_page = LoginPage(page)
        login_page.login_user()

    # Create an instance of the Ongoing Lock/Unlock page object
    lock_page = List_View_Ongoing_Lock_Unlock_Flight_Page(page)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View"):
        lock_page.navigate_to_list_view_page()

    # -------------------------------------------------------------------------
    # Step 2: Make sure the 'Ongoing' section tab is active
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Ongoing Section is Selected"):
        total_flights = lock_page.ensure_ongoing_section()
        assert total_flights > 0, "No flights available in Ongoing section."

    # -------------------------------------------------------------------------
    # Step 3: Find a flight card and ensure it starts in an unlocked state
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Locate Target Flight Card and Ensure Unlocked State"):
        flight_cards = lock_page.page.locator(lock_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        flight_number = lock_page.get_flight_number(target_flight)
        logger.info(f"Selected flight for test: '{flight_number}' in Ongoing section")

        # If the flight is already locked from a previous run, unlock it first so the test starts clean
        if lock_page.is_flight_locked(target_flight):
            logger.info(f"Flight '{flight_number}' is initially LOCKED. Resetting to UNLOCKED state first...")
            lock_page.unlock_flight(flight_card=target_flight, remarks="Resetting to unlocked state")
            lock_page.wait_for_lock_state(flight_card=target_flight, expected_locked=False, timeout_ms=10000)

    # -------------------------------------------------------------------------
    # Step 4: Lock the flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 4: Lock Flight '{flight_number}'"):
        logger.info(f"Proceeding to LOCK Flight '{flight_number}'...")
        lock_result = lock_page.lock_flight(
            flight_card=target_flight,
            reason="Test",
            remarks="Testing Flight"
        )
        assert lock_result["flight_number"], "Flight number could not be determined."
        assert lock_result["reason"] == "Test", "Reason did not match expected value 'Test'."
        assert lock_result["remarks"] == "Testing Flight", "Remarks did not match expected value 'Testing Flight'."

    # -------------------------------------------------------------------------
    # Step 5: Verify that the flight is now LOCKED
    # -------------------------------------------------------------------------
    with allure.step(f"Step 5: Verify Flight '{flight_number}' is in LOCKED State"):
        flight_cards = lock_page.page.locator(lock_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        is_locked_ok = lock_page.wait_for_lock_state(
            flight_card=target_flight,
            expected_locked=True,
            timeout_ms=10000
        )
        assert is_locked_ok, (
            f"Post-condition failed: Flight '{flight_number}' is NOT locked after locking action."
        )
        logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully LOCKED.")

    # -------------------------------------------------------------------------
    # Step 6: Unlock the flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 6: Unlock Flight '{flight_number}'"):
        logger.info(f"Proceeding to UNLOCK Flight '{flight_number}'...")
        flight_cards = lock_page.page.locator(lock_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        unlock_result = lock_page.unlock_flight(
            flight_card=target_flight,
            remarks="Testing Unlock"
        )
        assert unlock_result["remarks"] == "Testing Unlock", (
            "Remarks did not match expected value 'Testing Unlock'."
        )

    # -------------------------------------------------------------------------
    # Step 7: Verify that the flight is now UNLOCKED
    # -------------------------------------------------------------------------
    with allure.step(f"Step 7: Verify Flight '{flight_number}' is in UNLOCKED State"):
        flight_cards = lock_page.page.locator(lock_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        is_unlocked_ok = lock_page.wait_for_lock_state(
            flight_card=target_flight,
            expected_locked=False,
            timeout_ms=10000
        )
        assert is_unlocked_ok, (
            f"Post-condition failed: Flight '{flight_number}' is STILL locked after unlocking."
        )
        logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully UNLOCKED.")

    logger.info("=== Completed Test: Ongoing Section Sequential Lock & Unlock Flight successfully ===")
