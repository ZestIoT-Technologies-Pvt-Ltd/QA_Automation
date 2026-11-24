# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-23

import pytest
import allure
from pages.List_View.ListView_Incoming_Flag_Unflag_Flight_Page import ListView_Incoming_Flag_Unflag_Flight_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_ListView_Incoming_Flag_Unflag_Flight(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify end-to-end flight flagging and unflagging (First Flag -> Then Unflag) in the Incoming section.

    Steps:
    1. Prerequisite: Authenticate / Login to application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Ensure Incoming flights section is active and loaded.
    4. Step 3: Locate target flight card in Incoming section and ensure it starts unflagged (reset if needed).
    5. Step 4: Flag the flight (select flag from dropdown and click Save).
    6. Step 5: Verify and assert that the flight is now in FLAGGED state.
    7. Step 6: Unflag the flight (click unmark icon and confirm Unflag in dialog).
    8. Step 7: Verify and assert that the flight is now in UNFLAGGED state.
    """
    logger.info("Starting List View Sequential Flagging & Unflagging Test for Incoming section")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    flag_page = ListView_Incoming_Flag_Unflag_Flight_Page(page)

    # -------------------------------------------------------------------------
    # Step 1: Navigate to Flights List View Screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            flag_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully navigated to Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Make sure Incoming section is active
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Incoming Section is Loaded and Flights areLoaded"):
        flight_count = flag_page.ensure_incoming_section()
        with allure.step(f"2.1: Verify Incoming tab is active with flight cards displayed"):
            assert flight_count > 0, "No flights found in Incoming section."
        allure.attach(
            f"Active Section: Incoming\nTotal Available Flight Cards: {flight_count}",
            name="Incoming_Section_Overview",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Incoming section active with {flight_count} flights")

    # -------------------------------------------------------------------------
    # Step 3: Locate target flight card and ensure clean starting state
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Check Flight Card in Incoming Section and Ensure Unflagged State"):
        target_flight = flag_page.get_first_flight_card()
        flight_number = flag_page.get_flight_number(target_flight)
        logger.info(f"Selected Incoming flight for test: '{flight_number}'")

        with allure.step(f"3.1: Identify targeted flight on screen"):
            assert flight_number, "Failed to retrieve flight number in Incoming section."

        with allure.step(f"3.2: Check if Flight is already flagged"):
            is_initially_flagged = flag_page.is_flight_flagged(target_flight)

        if is_initially_flagged:
            with allure.step(f"3.3: Flight is initially FLAGGED. Resetting to UNFLAGGED state first"):
                flag_page.unflag_flight(target_flight)
                is_reset = flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=8000)
                assert is_reset, f"Failed to reset flight '{flight_number}' to unflagged state before starting."

        allure.attach(
            f"Section: Incoming\nTarget Flight: {flight_number}\nInitial Flag State: UNFLAGGED (Clean starting state)",
            name=f"{flight_number}_Initial_State",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 4: Flag the flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 4: Flag Flight via Flag Dropdown"):
        logger.info(f"Proceeding to FLAG Flight '{flight_number}'...")
        with allure.step("4.1: Click flag icon, open flag dropdown options, and select a flag"):
            result = flag_page.flag_flight(target_flight)

        with allure.step(f"4.2: Verify selected flag value -> Selected: '{result.get('selected_flag')}'"):
            assert result["selected_flag"], (
                f"Failed to select a flag for flight '{flight_number}' in Incoming section."
            )
            assert len(result["available_flags"]) > 0, (
                "No flag options returned from dropdown in Incoming section."
            )

        allure.attach(
            f"Flight: {flight_number}\n"
            f"Section: Incoming\n"
            f"Selected Flag: {result['selected_flag']}\n"
            f"Available Flag Options in Dropdown: {result['available_flags']}\n"
            f"Action: Flag selected and saved.",
            name=f"{flight_number}_Flag_Selection",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 5: Verify flight is flagged
    # -------------------------------------------------------------------------
    with allure.step(f"Step 5: Verify and Assert Flight is in FLAGGED State"):
        with allure.step("5.1: Wait for flagged indicator badge to appear on flight card"):
            target_flight = flag_page.get_first_flight_card()
            is_flagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=True, timeout_ms=10000)

        with allure.step("5.2: Check that flight card displays the selected flag badge"):
            assert is_flagged_ok, (
                f"Post-condition failed: Flight '{flight_number}' is NOT flagged after flagging action in Incoming."
            )

        allure.attach(
            f"Flight: {flight_number}\n"
            f"Section: Incoming\n"
            f"Expected State: FLAGGED\n"
            f"Applied Flag: {result['selected_flag']}\n"
            f"Verification Result: PASSED",
            name=f"{flight_number}_Flagged_Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(
            f"Verification Passed: Flight '{flight_number}' is now successfully FLAGGED with '{result['selected_flag']}'."
        )

    # -------------------------------------------------------------------------
    # Step 6: Unflag the flight
    # -------------------------------------------------------------------------
    with allure.step(f"Step 6: Unflag Flight via Confirmation Dialog"):
        logger.info(f"Proceeding to UNFLAG Flight '{flight_number}'...")
        with allure.step("6.1: Click unflag icon on flight card and confirm unflag in dialog"):
            target_flight = flag_page.get_first_flight_card()
            unflag_success = flag_page.unflag_flight(target_flight)

        with allure.step("6.2: Verify unflag dialog submission was successful"):
            assert unflag_success, f"Failed to perform unflag action for flight '{flight_number}' in Incoming."

        allure.attach(
            f"Flight: {flight_number}\n"
            f"Section: Incoming\n"
            f"Action: Clicked unmark flag icon and confirmed dialog.\n"
            f"Dialog Submission: Success",
            name=f"{flight_number}_Unflag_Action",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 7: Verify flight is unflagged
    # -------------------------------------------------------------------------
    with allure.step(f"Step 7: Verify and Assert Flight Returns to UNFLAGGED State"):
        with allure.step("7.1: Wait for flag indicator badge to detach from flight card"):
            target_flight = flag_page.get_first_flight_card()
            is_unflagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=10000)

        with allure.step("7.2: Assert that flight card returns to unflagged state"):
            assert is_unflagged_ok, (
                f"Post-condition failed: Flight '{flight_number}' is STILL flagged after unflagging in Incoming."
            )

        allure.attach(
            f"Flight: {flight_number}\n"
            f"Section: Incoming\n"
            f"Expected State: UNFLAGGED\n"
            f"Verification Result: PASSED",
            name=f"{flight_number}_Unflagged_Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully UNFLAGGED.")

    logger.info("=== Completed Test: Incoming Section Flag & Unflag Test successfully ===")
