# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

import pytest
import allure
from pages.List_View.List_View_Ongoing_Lock_Unlock_Flight_Page import (
    List_View_Ongoing_Lock_Unlock_Flight_Page,
)
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_List_View_Ongoing_Lock_Unlock_Flight(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify end-to-end flight locking and unlocking (First Lock -> Then Unlock) in Flights List View (Ongoing Section).

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View.
    3. Ensure Ongoing Section is active (do not navigate to any other section).
    4. Locate the target flight card on the dashboard and ensure it is in an unlocked state (reset if initially locked).
    5. Lock the flight by clicking Three-Dots menu ('more_vert') -> 'Lock Flight', filling Reason ('Test') and Remarks ('Testing Flight'), and clicking Lock.
    6. Verify and assert that the flight is now in LOCKED state (lock icon button is displayed).
    7. Unlock the flight by clicking the lock icon button on the flight card, entering Remarks ('Testing Unlock'), and clicking Unlock.
    8. Verify and assert that the flight is now in UNLOCKED state (lock icon button is absent).
    """
    logger.info("Starting List View Ongoing Section Sequential Lock & Unlock Flight Test")

    lock_page = List_View_Ongoing_Lock_Unlock_Flight_Page(page)

    with allure.step("Step 1: Navigate to Flights List View"):
        lock_page.navigate_to_list_view_page()

    with allure.step("Step 2: Ensure Ongoing Section is Selected"):
        total_flights = lock_page.ensure_ongoing_section()
        assert total_flights > 0, "No flights available in Ongoing section."

    with allure.step("Step 3: Locate Target Flight Card and Ensure Unlocked State"):
        flight_cards = lock_page.page.locator(lock_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        flight_number = lock_page.get_flight_number(target_flight)
        logger.info(f"Selected flight for test: '{flight_number}' in Ongoing section")

        # Ensure flight is in UNLOCKED state before starting sequence
        if lock_page.is_flight_locked(target_flight):
            logger.info(f"Flight '{flight_number}' is initially LOCKED. Resetting to UNLOCKED state first...")
            lock_page.unlock_flight(flight_card=target_flight, remarks="Resetting to unlocked state")
            lock_page.wait_for_lock_state(flight_card=target_flight, expected_locked=False, timeout_ms=10000)

    # FIRST: LOCK THE FLIGHT
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

    # VERIFY FLIGHT IS LOCKED
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

    # SECOND: UNLOCK THE FLIGHT
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

    # VERIFY FLIGHT IS UNLOCKED
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

    logger.info("List View Ongoing Section Sequential Lock & Unlock Flight Test completed successfully")
