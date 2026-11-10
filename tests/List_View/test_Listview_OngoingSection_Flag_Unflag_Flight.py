# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

import pytest
import allure
from pages.List_View.ListView_Ongoing_Flag_Unflag_Flight_Page import Listview_OngoingSection_Flag_Unflag_Flight
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_Listview_OngoingSection_FlagUnflagFlight(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify end-to-end flight flagging and unflagging (First Flag -> Then Unflag) across Ongoing and Incoming sections.

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View.
    3. Iterate through Ongoing and Incoming sections:
       a. Switch to the section tab.
       b. Validate flight cards are visible.
       c. Locate target flight card and ensure it is initially unflagged (reset by unflagging if already flagged).
       d. Flag the flight (select flag from dropdown by text value, click Save).
       e. Verify and assert that the flight is now in FLAGGED state.
       f. Unflag the flight (click unmark icon, confirm Unflag in dialog).
       g. Verify and assert that the flight is now in UNFLAGGED state.
    """
    logger.info("Starting List View Sequential Flagging & Unflagging Test for Ongoing and Incoming sections")

    flag_page = Listview_OngoingSection_Flag_Unflag_Flight(page)

    with allure.step("Step 1: Navigate to Flights List View"):
        flag_page.navigate_to_list_view_page()

    summary_records = []

    # Iterate strictly through Ongoing and Incoming sections
    for section in flag_page.SECTIONS:
        section_name = section["name"]
        tab_locator = section["tab"]

        with allure.step(f"Section '{section_name}': Sequential Flag & Unflag Workflow"):
            logger.info(f"==================== Section: {section_name} ====================")

            # 2a. Switch to Section Tab
            with allure.step(f"Step 2: Switch to '{section_name}' Section Tab"):
                flag_page.switch_to_section(section_name, tab_locator)

            # 2b. Validate Flights Visibility
            with allure.step(f"Step 3: Validate Flights Visibility in '{section_name}'"):
                has_flights = flag_page.flights_are_visible(section_name)
                if not has_flights:
                    logger.warning(f"No flights found in {section_name} section. Skipping.")
                    continue

                flight_count = flag_page.count_of_flights()
                logger.info(f"Number of flights available in {section_name}: {flight_count}")

            # 2c. Locate the target flight card
            with allure.step(f"Step 4: Locate Target Flight Card in '{section_name}'"):
                flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
                target_flight = flight_cards.first
                flight_number = flag_page.get_flight_number(target_flight)
                logger.info(f"Selected flight for test: '{flight_number}' in {section_name}")

                # Ensure flight is in UNFLAGGED state before starting sequence
                if flag_page.is_flight_flagged(target_flight):
                    logger.info(f"Flight '{flight_number}' is initially FLAGGED. Resetting to UNFLAGGED state first...")
                    flag_page.unflag_flight(target_flight)
                    flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=8000)

            # 2d. FIRST: FLAG THE FLIGHT
            with allure.step(f"Step 5: Flag Flight '{flight_number}'"):
                logger.info(f"Proceeding to FLAG Flight '{flight_number}'...")
                result = flag_page.flag_flight(target_flight)

                assert result["selected_flag"], (
                    f"Failed to select a flag for flight '{flight_number}' in {section_name} section."
                )
                assert len(result["available_flags"]) > 0, (
                    f"No flag options returned from dropdown in {section_name} section."
                )

            # 2e. VERIFY FLIGHT IS FLAGGED
            with allure.step(f"Step 6: Verify Flight '{flight_number}' is FLAGGED"):
                flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
                target_flight = flight_cards.first
                is_flagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=True, timeout_ms=10000)
                assert is_flagged_ok, (
                    f"Post-condition failed: Flight '{flight_number}' is NOT flagged after flagging action."
                )
                logger.info(
                    f"Verification Passed: Flight '{flight_number}' is now successfully FLAGGED with '{result['selected_flag']}'."
                )

            # 2f. SECOND: UNFLAG THE FLIGHT
            with allure.step(f"Step 7: Unflag Flight '{flight_number}'"):
                logger.info(f"Proceeding to UNFLAG Flight '{flight_number}'...")
                flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
                target_flight = flight_cards.first
                unflag_success = flag_page.unflag_flight(target_flight)
                assert unflag_success, f"Failed to perform unflag action for flight '{flight_number}'."

            # 2g. VERIFY FLIGHT IS UNFLAGGED
            with allure.step(f"Step 8: Verify Flight '{flight_number}' is UNFLAGGED"):
                flight_cards = flag_page.page.locator(flag_page.FLIGHT_ROW_CARDS)
                target_flight = flight_cards.first
                is_unflagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=10000)
                assert is_unflagged_ok, (
                    f"Post-condition failed: Flight '{flight_number}' is STILL flagged after unflagging."
                )
                logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully UNFLAGGED.")

            summary_records.append({
                "section": section_name,
                "flight": flight_number,
                "flag_selected": result["selected_flag"],
                "flagged_status": "PASSED",
                "unflagged_status": "PASSED",
            })

    logger.info("==================== Execution Summary ====================")
    for record in summary_records:
        logger.info(
            f"Section: {record['section']} | Flight: {record['flight']} | "
            f"Flag Selected: {record['flag_selected']} | Flagged: {record['flagged_status']} | "
            f"Unflagged: {record['unflagged_status']}"
        )

    assert len(summary_records) > 0, (
        "No flights were processed in Ongoing or Incoming sections. Please verify flight availability."
    )
    logger.info("List View Sequential Flag & Unflag Test completed successfully")
    logger.info("List View Conditional Flagging / Unflagging Test completed successfully")
