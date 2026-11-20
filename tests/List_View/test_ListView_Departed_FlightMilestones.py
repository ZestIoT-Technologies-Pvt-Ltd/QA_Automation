# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-19

"""
==============  INTRODUCTION ================
Test Scenario: Verify whether milestone sequence, completion status bar and actual timestamps are displayed.

What this test does:
This test verifies that departed flights show their flight milestone progression correctly:
1. Logs into the AviLeap application with valid credentials.
2. Navigates to the Flights List View screen.
3. Switches to the 'Departed' section tab and confirms departed flight cards are loaded.
4. For the departed flights shown on screen:
   a. Clicks the ellipsis ('more_vert') menu on the flight card.
   b. Clicks 'Flight Milestones' to open the popup screen.
   c. Verifies that milestones are present in the popup.
   d. Checks the chronological milestone order:
      1) Ten Nautical Miles
      2) Touchdown
      3) Airborne (if airborne)
   e. Verifies that the milestone completion status bar / milestone items are visible.
   f. Verifies that actual timestamps (e.g. '14:30') are displayed for the milestones.
   g. Closes the popup and clicks anywhere on the screen to dismiss leftover tooltips.
5. Summarizes validation results and confirms all inspected flights passed.
"""

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
    Test Scenario: Verify milestone sequence, completion status bar, and actual timestamps for departed flights.
    """
    logger.info("=== Starting Test: Departed Section Flight Milestones Validation ===")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    # Create an instance of the Departed Flight Milestones page object
    milestones_page = ListView_Departed_FlightMilestones_Page(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View dashboard screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        # Clicks the main navigation menu and selects Flights
        milestones_page.navigate_to_list_view_page()

    # -------------------------------------------------------------------------
    # Step 2: Make sure the 'Departed' section tab is active and flights are visible
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Departed Section is Active and Flights are Loaded"):
        # Clicks the 'Departed' tab and counts the loaded flight cards
        total_flights = milestones_page.ensure_departed_section_loaded()
        assert total_flights > 0, "No flight cards loaded in the Departed section."
        logger.info(f"Departed section active with {total_flights} flight cards")

    # -------------------------------------------------------------------------
    # Step 3: Validate Flight Milestones across departed flights
    # -------------------------------------------------------------------------
    card_loc = milestones_page.page.locator(milestones_page.FLIGHT_ROW_CARDS)
    # Check up to 5 departed flights to ensure thorough coverage
    flights_to_inspect = min(card_loc.count(), 5)
    logger.info(f"Inspecting Flight Milestones across {flights_to_inspect} departed flight cards")

    validation_results = []
    failed_flights = []

    with allure.step(f"Step 3: Validate Milestones across {flights_to_inspect} Departed Flight Cards"):
        for i in range(flights_to_inspect):
            card = card_loc.nth(i)
            flight_num = milestones_page.get_flight_number(card)
            with allure.step(f"Step 3.{i+1}: Validate Flight Milestones for Flight '{flight_num}'"):
                # Validates milestones popup, sequence, completion status bar, and actual timestamps
                res = milestones_page.validate_flight_milestones_card(card)
                validation_results.append(res)
                if not res["passed"]:
                    failed_flights.append(res)

                # Ensure popup is fully closed and neutral screen click is performed before moving to the next flight
                milestones_page.close_flight_milestones_popup()
                milestones_page.dismiss_lingering_tooltip()
                milestones_page.page.wait_for_timeout(500)

    # -------------------------------------------------------------------------
    # Step 4: Summary assertions across all inspected flights
    # -------------------------------------------------------------------------
    with allure.step("Step 4: Verify Milestone Sequence, Status Bar, and Timestamps"):
        passed_count = sum(1 for r in validation_results if r["passed"])
        failed_count = len(failed_flights)

        logger.info("==================== FLIGHT MILESTONES VALIDATION SUMMARY ====================")
        logger.info(f"Total Departed Flights Inspected: {len(validation_results)}")
        logger.info(f"Passed: {passed_count} | Failed: {failed_count}")

        for r in validation_results:
            m = r["milestones_data"]
            logger.info(
                f"Flight '{r['flight_number']}': Passed={r['passed']}, "
                f"SequenceCorrect={m['sequence_correct']}, "
                f"StatusBar={m['status_bar_displayed']}, "
                f"HasTimestamps={m['has_actual_timestamps']} (Found={m['timestamps_found']})"
            )

        assert failed_count == 0, (
            f"Flight Milestones validation failed for {failed_count} flight(s): "
            f"{[f['flight_number'] + ' -> ' + '; '.join(f['reasons']) for f in failed_flights]}"
        )

    logger.info("=== Completed Test: Departed Section Flight Milestones Validation successfully ===")
