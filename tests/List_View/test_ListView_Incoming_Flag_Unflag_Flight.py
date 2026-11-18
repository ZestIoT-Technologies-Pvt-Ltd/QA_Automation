# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

import pytest
import allure
from pages.List_View.ListView_Incoming_Flag_Unflag_Flight_Page import ListView_Incoming_Flag_Unflag_Flight_Page
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_ListView_Incoming_Flag_Unflag_Flight(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify end-to-end flight flagging and unflagging (First Flag -> Then Unflag) in the Incoming section.

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View.
    3. Ensure Incoming section is active.
    4. Validate flight cards are visible.
    5. Locate target flight card and ensure it is initially unflagged (reset by unflagging if already flagged).
    6. Flag the flight (select flag from dropdown by text value, click Save).
    7. Verify and assert that the flight is now in FLAGGED state.
    8. Unflag the flight (click unmark icon, confirm Unflag in dialog).
    9. Verify and assert that the flight is now in UNFLAGGED state.
    """
    logger.info("Starting List View Sequential Flagging & Unflagging Test for Incoming section")

    flag_page = ListView_Incoming_Flag_Unflag_Flight_Page(page)

    with allure.step("Step 1: Navigate to Flights List View"):
        flag_page.navigate_to_list_view_page()

    with allure.step("Step 2: Ensure Incoming Section is Active"):
        flight_count = flag_page.ensure_incoming_section()
        assert flight_count > 0, "No flights found in Incoming section."
        logger.info(f"Incoming section active with {flight_count} flights")

    with allure.step("Step 3: Locate Target Flight Card in Incoming Section"):
        flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        flight_number = flag_page.get_flight_number(target_flight)
        logger.info(f"Selected Incoming flight for test: '{flight_number}'")

        # Ensure flight is in UNFLAGGED state before starting sequence
        if flag_page.is_flight_flagged(target_flight):
            logger.info(f"Flight '{flight_number}' is initially FLAGGED. Resetting to UNFLAGGED state first...")
            flag_page.unflag_flight(target_flight)
            flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=8000)

    # FIRST: FLAG THE FLIGHT
    with allure.step(f"Step 4: Flag Flight '{flight_number}'"):
        logger.info(f"Proceeding to FLAG Flight '{flight_number}'...")
        result = flag_page.flag_flight(target_flight)

        assert result["selected_flag"], (
            f"Failed to select a flag for flight '{flight_number}' in Incoming section."
        )
        assert len(result["available_flags"]) > 0, (
            "No flag options returned from dropdown in Incoming section."
        )

    # VERIFY FLIGHT IS FLAGGED
    with allure.step(f"Step 5: Verify Flight '{flight_number}' is FLAGGED"):
        flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        is_flagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=True, timeout_ms=10000)
        assert is_flagged_ok, (
            f"Post-condition failed: Flight '{flight_number}' is NOT flagged after flagging action."
        )
        logger.info(
            f"Verification Passed: Flight '{flight_number}' is now successfully FLAGGED with '{result['selected_flag']}'."
        )

    # SECOND: UNFLAG THE FLIGHT
    with allure.step(f"Step 6: Unflag Flight '{flight_number}'"):
        logger.info(f"Proceeding to UNFLAG Flight '{flight_number}'...")
        flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        unflag_success = flag_page.unflag_flight(target_flight)
        assert unflag_success, f"Failed to perform unflag action for flight '{flight_number}'."

    # VERIFY FLIGHT IS UNFLAGGED
    with allure.step(f"Step 7: Verify Flight '{flight_number}' is UNFLAGGED"):
        flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
        target_flight = flight_cards.first
        is_unflagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=10000)
        assert is_unflagged_ok, (
            f"Post-condition failed: Flight '{flight_number}' is STILL flagged after unflagging."
        )
        logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully UNFLAGGED.")

    logger.info("=== Completed Test: Incoming Section Flag & Unflag Test successfully ===")
