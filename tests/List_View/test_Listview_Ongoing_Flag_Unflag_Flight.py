# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-23

import pytest
import allure
from pages.List_View.ListView_Ongoing_Flag_Unflag_Flight_Page import Listview_OngoingSection_Flag_Unflag_Flight
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_Listview_OngoingSection_FlagUnflagFlight(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify end-to-end flight flagging and unflagging (First Flag -> Then Unflag) across Ongoing and Incoming sections.

    Steps:
    1. Prerequisite: Authenticate / Login to application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Iterate through Ongoing and Incoming sections:
       a. Step 2: Switch to the section tab.
       b. Step 3: Validate flight cards are visible and loaded.
       c. Step 4: Locate target flight card and ensure it starts unflagged (reset if needed).
       d. Step 5: Flag the flight (select flag from dropdown and click Save).
       e. Step 6: Verify and assert that the flight is now in FLAGGED state.
       f. Step 7: Unflag the flight (click unmark icon and confirm Unflag in dialog).
       g. Step 8: Verify and assert that the flight is now in UNFLAGGED state.
    """
    logger.info("Starting List View Sequential Flagging & Unflagging Test for Ongoing and Incoming sections")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    flag_page = Listview_OngoingSection_Flag_Unflag_Flight(page)

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

    summary_records = []

    # Iterate strictly through Ongoing and Incoming sections
    for section in flag_page.SECTIONS:
        section_name = section["name"]
        tab_locator = section["tab"]

        with allure.step(f"Section '{section_name}': Flag & Unflag Workflow"):
            logger.info(f"==================== Section: {section_name} ====================")

            # -----------------------------------------------------------------
            # Step 2: Switch to Section Tab
            # -----------------------------------------------------------------
            with allure.step(f"Step 2: Switch to '{section_name}' Section Tab"):
                with allure.step(f"2.1: Click on the '{section_name}' tab"):
                    flag_page.switch_to_section(section_name, tab_locator)
                allure.attach(
                    f"Active Section Tab: {section_name}",
                    name=f"{section_name}_Tab_Status",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # -----------------------------------------------------------------
            # Step 3: Validate Flights Visibility
            # -----------------------------------------------------------------
            with allure.step(f"Step 3: Validate Flights are Visible in '{section_name}' Section"):
                with allure.step(f"3.1: Check if flight cards are visible in '{section_name}'"):
                    has_flights = flag_page.flights_are_visible(section_name)
                if not has_flights:
                    logger.warning(f"No flights found in {section_name} section. Skipping.")
                    allure.attach(
                        f"Section '{section_name}' has 0 flight cards loaded. Skipping workflow for this section.",
                        name=f"{section_name}_No_Flights",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    continue

                flight_count = flag_page.count_of_flights()
                allure.attach(
                    f"Section: {section_name}\nTotal Available Flight Cards: {flight_count}",
                    name=f"{section_name}_Flight_Count",
                    attachment_type=allure.attachment_type.TEXT,
                )
                logger.info(f"Number of flights available in {section_name}: {flight_count}")

            # -----------------------------------------------------------------
            # Step 4: Locate Target Flight Card and Ensure Unflagged State
            # -----------------------------------------------------------------
            with allure.step(f"Step 4: Check Flight Card in '{section_name}' and Ensure Unflagged State"):
                target_flight = flag_page.get_first_flight_card()
                flight_number = flag_page.get_flight_number(target_flight)
                logger.info(f"Selected flight for test: '{flight_number}' in {section_name}")

                with allure.step(f"4.1: Identify target flight on screen -> Flight Number: '{flight_number}'"):
                    assert flight_number, f"Failed to retrieve flight number in {section_name} section."

                with allure.step(f"4.2: Check if Flight is already flagged"):
                    is_initially_flagged = flag_page.is_flight_flagged(target_flight)

                if is_initially_flagged:
                    with allure.step(f"4.3: Flight is initially FLAGGED. Resetting to UNFLAGGED state first"):
                        flag_page.unflag_flight(target_flight)
                        is_reset = flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=8000)
                        assert is_reset, f"Failed to reset flight '{flight_number}' to unflagged state before starting."

                allure.attach(
                    f"Section: {section_name}\nTarget Flight: {flight_number}\nInitial Flag State: UNFLAGGED (Clean starting state)",
                    name=f"{section_name}_{flight_number}_Initial_State",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # -----------------------------------------------------------------
            # Step 5: Flag the Flight
            # -----------------------------------------------------------------
            with allure.step(f"Step 5: Flag Flight via Flag Dropdown"):
                with allure.step("5.1: Click flag icon, open flag dropdown options, and select a flag"):
                    result = flag_page.flag_flight(target_flight)

                with allure.step(f"5.2: Verify selected flag value -> Selected: '{result.get('selected_flag')}'"):
                    assert result["selected_flag"], (
                        f"Failed to select a flag for flight '{flight_number}' in {section_name} section."
                    )
                    assert len(result["available_flags"]) > 0, (
                        f"No flag options returned from dropdown in {section_name} section."
                    )

                allure.attach(
                    f"Flight: {flight_number}\n"
                    f"Section: {section_name}\n"
                    f"Selected Flag: {result['selected_flag']}\n"
                    f"Available Flag Options in Dropdown: {result['available_flags']}\n"
                    f"Action: Flag selected and saved.",
                    name=f"{section_name}_{flight_number}_Flag_Selection",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # -----------------------------------------------------------------
            # Step 6: Verify Flight is in Flagged State
            # -----------------------------------------------------------------
            with allure.step(f"Step 6: Verify and Assert Flight is in FLAGGED State"):
                with allure.step("6.1: Wait for flagged indicator badge to appear on flight card"):
                    target_flight = flag_page.get_first_flight_card()
                    is_flagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=True, timeout_ms=10000)

                with allure.step("6.2: Assert that flight card displays the selected flag badge"):
                    assert is_flagged_ok, (
                        f"Post-condition failed: Flight '{flight_number}' is NOT flagged after flagging action in {section_name}."
                    )

                allure.attach(
                    f"Flight: {flight_number}\n"
                    f"Section: {section_name}\n"
                    f"Expected State: FLAGGED\n"
                    f"Applied Flag: {result['selected_flag']}\n"
                    f"Verification Result: PASSED",
                    name=f"{section_name}_{flight_number}_Flagged_Verification",
                    attachment_type=allure.attachment_type.TEXT,
                )
                logger.info(
                    f"Verification Passed: Flight '{flight_number}' is now successfully FLAGGED with '{result['selected_flag']}'."
                )

            # -----------------------------------------------------------------
            # Step 7: Unflag the Flight
            # -----------------------------------------------------------------
            with allure.step(f"Step 7: Unflag Flight via Confirmation Dialog"):
                with allure.step("7.1: Click unflag icon on flight card and confirm unflag in dialog"):
                    target_flight = flag_page.get_first_flight_card()
                    unflag_success = flag_page.unflag_flight(target_flight)

                with allure.step("7.2: Verify unflag dialog submission was successful"):
                    assert unflag_success, f"Failed to perform unflag action for flight '{flight_number}' in {section_name}."

                allure.attach(
                    f"Flight: {flight_number}\n"
                    f"Section: {section_name}\n"
                    f"Action: Clicked unmark flag icon and confirmed dialog.\n"
                    f"Dialog Submission: Success",
                    name=f"{section_name}_{flight_number}_Unflag_Action",
                    attachment_type=allure.attachment_type.TEXT,
                )

            # -----------------------------------------------------------------
            # Step 8: Verify Flight is in Unflagged State
            # -----------------------------------------------------------------
            with allure.step(f"Step 8: Verify and Assert Flight Returns to UNFLAGGED State"):
                with allure.step("8.1: Wait for flag indicator badge to detach from flight card"):
                    target_flight = flag_page.get_first_flight_card()
                    is_unflagged_ok = flag_page.wait_for_flag_state(target_flight, expected_flagged=False, timeout_ms=10000)

                with allure.step("8.2: Assert that flight card returns to unflagged state"):
                    assert is_unflagged_ok, (
                        f"Post-condition failed: Flight '{flight_number}' is STILL flagged after unflagging in {section_name}."
                    )

                allure.attach(
                    f"Flight: {flight_number}\n"
                    f"Section: {section_name}\n"
                    f"Expected State: UNFLAGGED\n"
                    f"Verification Result: PASSED",
                    name=f"{section_name}_{flight_number}_Unflagged_Verification",
                    attachment_type=allure.attachment_type.TEXT,
                )
                logger.info(f"Verification Passed: Flight '{flight_number}' is now successfully UNFLAGGED in {section_name}.")

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
