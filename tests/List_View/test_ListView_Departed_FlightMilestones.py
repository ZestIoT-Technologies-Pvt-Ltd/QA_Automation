# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

"""
==============  INTRODUCTION ================
Test Scenario: Verify whether milestone sequence, completion status bar and actual timestamps are displayed.

Scenario Details:
1. In the Departed section, in the 3-dots ('more_vert') menu, click 'Flight Milestones'.
2. In the Flight Milestones popup screen:
   a. Check that milestones are present in the popup.
   b. Check the sequence of milestones:
      1) Ten Nautical Miles
      2) Touchdown
      3) Airborne (if airborne)
   c. Check that the milestone completion status bar / milestone items are displayed.
   d. Check that actual timestamps are displayed for the milestones.
3. Close the popup and click anywhere on the screen to dismiss the menu tooltip before
   moving to the next flight card.
"""

import pytest
import allure
from pages.List_View.ListView_Departed_FlightMilestones_Page import ListView_Departed_FlightMilestones_Page
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_listview_departed_flight_milestones(page):
    """
    Test Scenario: Verify milestone sequence, completion status bar, and actual timestamps
    for departed flights.
    """
    logger.info("Starting Departed Section Flight Milestones Validation Test")

    milestones_page = ListView_Departed_FlightMilestones_Page(page, None)

    # Step 1: Navigate to Flights List View Dashboard
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        milestones_page.navigate_to_list_view_page()

    # Step 2: Ensure Departed Section is active and flights are loaded
    with allure.step("Step 2: Ensure Departed Section is Active and Flights are Loaded"):
        total_flights = milestones_page.ensure_departed_section_loaded()
        assert total_flights > 0, "No flight cards loaded in the Departed section."
        logger.info(f"Departed section active with {total_flights} flight cards")

    # Step 3: Validate Flight Milestones across departed flights
    card_loc = milestones_page.page.locator(milestones_page.FLIGHT_ROW_CARDS)
    flights_to_inspect = min(card_loc.count(), 5)
    logger.info(f"Inspecting Flight Milestones across {flights_to_inspect} departed flight cards")

    validation_results = []
    failed_flights = []

    with allure.step(f"Step 3: Validate Milestones across {flights_to_inspect} Departed Flight Cards"):
        for i in range(flights_to_inspect):
            card = card_loc.nth(i)
            res = milestones_page.validate_flight_milestones_card(card)
            validation_results.append(res)
            if not res["passed"]:
                failed_flights.append(res)

            # Ensure popup is fully closed and tooltip dismissed before moving to next flight
            milestones_page.close_flight_milestones_popup()
            milestones_page.dismiss_lingering_tooltip()
            milestones_page.page.wait_for_timeout(500)

    # Step 4: Summary assertions
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

    logger.info("Departed Section Flight Milestones Validation Test completed successfully")
