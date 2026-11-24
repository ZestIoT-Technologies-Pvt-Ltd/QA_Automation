# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

import pytest
import allure
from pages.List_View.ListView_Departed_FlightMilestones_Page import ListView_Departed_FlightMilestones_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_listview_departed_flight_milestones(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify that departed flights show their milestone sequence, completion status bar, and actual timestamps correctly.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Ensure Departed section is active and flight cards are loaded.
    4. Step 3: Open milestones popup for departed flights and verify:
       a. Milestone sequence order (Ten Nautical Miles, Touchdown, Airborne).
       b. Milestone completion status bar.
       c. Actual timestamps displayed for milestones.
    5. Step 4: Verify overall milestone results across all inspected flights.
    """
    logger.info("=== Starting Test: Departed Section Flight Milestones Validation ===")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    milestones_page = ListView_Departed_FlightMilestones_Page(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View dashboard screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            milestones_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Make sure the 'Departed' section tab is active and flights are visible
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Departed Section is Active and Flights are Loaded"):
        total_flights = milestones_page.ensure_departed_section_loaded()
        with allure.step(f"2.1: Check Departed tab is Opened with flight cards loaded"):
            assert total_flights > 0, "No flight cards loaded in the Departed section."
        allure.attach(
            f"Active Section: Departed\nTotal Flight Cards Loaded: {total_flights}",
            name="Departed_Section_Status",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Departed section active with {total_flights} flight cards")

    # -------------------------------------------------------------------------
    # Step 3: Validate Flight Milestones across departed flights
    # -------------------------------------------------------------------------
    card_loc = milestones_page.page.locator(milestones_page.FLIGHT_ROW_CARDS)
    flights_to_inspect = min(card_loc.count(), 5)
    logger.info(f"Inspecting Flight Milestones across {flights_to_inspect} departed flight cards")

    validation_results = []
    failed_flights = []

    with allure.step(f"Step 3: Validate Milestones across Departed Flight Cards"):
        for i in range(flights_to_inspect):
            card = card_loc.nth(i)
            flight_num = milestones_page.get_flight_number(card) or f"Flight {i + 1}"

            with allure.step(f"Step 3.1: Validate Flight Milestones for Flight"):
                with allure.step(f"Open Flight Milestones popup and verify milestone order, and timestamps"):
                    res = milestones_page.validate_flight_milestones_card(card)
                    validation_results.append(res)
                    if not res["passed"]:
                        failed_flights.append(res)

                with allure.step(f"Close popup drawer and dismiss tooltips"):
                    milestones_page.close_flight_milestones_popup()
                    milestones_page.dismiss_lingering_tooltip()
                    milestones_page.page.wait_for_timeout(500)

                allure.attach(
                    f"Flight: {flight_num}\n"
                    f"Sequence Correct: {res['milestones_data']['sequence_correct']}\n"
                    f"Status Bar Displayed: {res['milestones_data']['status_bar_displayed']}\n"
                    f"Timestamps Found: {res['milestones_data']['timestamps_found']}\n"
                    f"Passed: {res['passed']}",
                    name=f"{flight_num}_Milestones_Summary",
                    attachment_type=allure.attachment_type.TEXT,
                )

    # -------------------------------------------------------------------------
    # Step 4: Summary assertions across all inspected flights
    # -------------------------------------------------------------------------
    with allure.step("Step 4: Verify Milestone Sequence, and Timestamps Summary"):
        passed_count = sum(1 for r in validation_results if r["passed"])
        failed_count = len(failed_flights)

        with allure.step(f"4.1: Assert milestone failures across inspected flights"):
            assert failed_count == 0, (
                f"Flight Milestones validation failed for {failed_count} flight(s): "
                f"{[f['flight_number'] + ' -> ' + '; '.join(f['reasons']) for f in failed_flights]}"
            )

        allure.attach(
            f"Total Departed Flights Inspected: {len(validation_results)}\n"
            f"Passed: {passed_count}\n"
            f"Failed: {failed_count}\n"
            f"Status: Milestone sequence, status bar, and actual timestamps validated successfully.",
            name="Overall_Milestones_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )

        logger.info("==================== FLIGHT MILESTONES VALIDATION SUMMARY ====================")
        logger.info(f"Total Departed Flights Inspected: {len(validation_results)}")
        logger.info(f"Passed: {passed_count} | Failed: {failed_count}")

    logger.info("=== Completed Test: Departed Section Flight Milestones Validation successfully ===")
