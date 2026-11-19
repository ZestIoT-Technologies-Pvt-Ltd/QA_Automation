# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

"""
==============  INTRODUCTION ================
Test Scenario: Verify Flight Section Placement and Transitions Based on On-Block (ONBL) and Off-Block (OFBL) Times.

Business Rules & Test Criteria:
1. Ongoing Section:
   - If the flight is having the On-Block time (ONBL) and DOES NOT have the Off-Block time (OFBL),
     then the flight should be present in the Ongoing Section (turnaround in progress).
2. Incoming Section:
   - If the flight is NOT having On-Block time and NOT having Off-Block time,
     then the flight should be present in the Incoming Section (en route / arriving inbound).
3. Departed Section:
   - If the flight is having BOTH the On-Block time and Off-Block time,
     then the flight should be present in the Departed Section (turnaround completed, pushed back).

Steps:
1. Prerequisite: Authenticate / Login to application using LoginPage.login_user().
2. Navigate to Flights List View dashboard.
3. Validate Ongoing Section:
   - Ensure Ongoing section is loaded.
   - For flight cards in Ongoing, verify that On-Block time (ONBL) is present and Off-Block time (OFBL) is absent.
4. Validate Incoming Section:
   - Switch to Incoming section.
   - For flight cards in Incoming, verify that neither On-Block nor Off-Block time is present.
5. Validate Departed Section:
   - Switch to Departed section.
   - For flight cards in Departed, verify that both On-Block and Off-Block times are present.
6. Assert zero section rule violations across all inspected flights.
"""

import pytest
import allure
from pages.List_View.ListView_Incoming_FlightTransition_Pages import ListView_Incoming_FlightTransition_Pages
from pages.Login.Login_Page import LoginPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_listview_incoming_flight_transition(page):
    """
    Test Scenario: Verify that flight presence across Incoming, Ongoing, and Departed sections strictly follows the On-Block (ONBL) and Off-Block (OFBL) lifecycle rules.
    """
    logger.info("Starting Flights List View Section Transition & Block-Time Rules Validation Test")

    with allure.step("Prerequisite: Login to application"):
        login_page = LoginPage(page)
        login_page.login_user()

    transition_page = ListView_Incoming_FlightTransition_Pages(page, None)

    # Step 1: Navigate to Flights List View Dashboard
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        transition_page.navigate_to_list_view_page()

    # Step 2: Validate Ongoing Section (Has On-Block time, NO Off-Block time)
    with allure.step("Step 2: Validate Ongoing Section (Has ONBL, NO OFBL)"):
        logger.info("--- Validating Ongoing Section Flights ---")
        ongoing_summary = transition_page.validate_section_flights("Ongoing", max_flights=15)
        logger.info(
            f"Ongoing Summary: Inspected={ongoing_summary['inspected_count']}, "
            f"Passed={ongoing_summary['passed_count']}, Failed={ongoing_summary['failed_count']}"
        )

        assert ongoing_summary["total_cards"] > 0, (
            "No flight cards loaded in the Ongoing section."
        )
        assert ongoing_summary["failed_count"] == 0, (
            f"Ongoing section block-time violations detected in {ongoing_summary['failed_count']} flights: "
            f"{[f['flight_number'] + ' -> ' + f['reason'] for f in ongoing_summary['failed_cards']]}"
        )

    # Step 3: Validate Incoming Section (NO On-Block time, NO Off-Block time)
    with allure.step("Step 3: Validate Incoming Section (NO ONBL, NO OFBL)"):
        logger.info("--- Validating Incoming Section Flights ---")
        incoming_summary = transition_page.validate_section_flights("Incoming", max_flights=10)
        logger.info(
            f"Incoming Summary: Inspected={incoming_summary['inspected_count']}, "
            f"Passed={incoming_summary['passed_count']}, Failed={incoming_summary['failed_count']}"
        )

        if incoming_summary["inspected_count"] > 0:
            assert incoming_summary["failed_count"] == 0, (
                f"Incoming section block-time violations detected in {incoming_summary['failed_count']} flights: "
                f"{[f['flight_number'] + ' -> ' + f['reason'] for f in incoming_summary['failed_cards']]}"
            )
        else:
            logger.info("Incoming section currently has 0 flights loaded; rule check bypassed.")

    # Step 4: Validate Departed Section (Has BOTH On-Block and Off-Block times)
    with allure.step("Step 4: Validate Departed Section (Has BOTH ONBL and OFBL)"):
        logger.info("--- Validating Departed Section Flights ---")
        departed_summary = transition_page.validate_section_flights("Departed", max_flights=10)
        logger.info(
            f"Departed Summary: Inspected={departed_summary['inspected_count']}, "
            f"Passed={departed_summary['passed_count']}, Failed={departed_summary['failed_count']}"
        )

        if departed_summary["inspected_count"] > 0:
            assert departed_summary["failed_count"] == 0, (
                f"Departed section block-time violations detected in {departed_summary['failed_count']} flights: "
                f"{[f['flight_number'] + ' -> ' + f['reason'] for f in departed_summary['failed_cards']]}"
            )
        else:
            logger.info("Departed section currently has 0 flights loaded; rule check bypassed.")

    # Step 5: Overall Verification & Summary Logging
    with allure.step("Step 5: Verify Overall Flight Transition Rules Across All Sections"):
        total_inspected = (
            ongoing_summary["inspected_count"]
            + incoming_summary["inspected_count"]
            + departed_summary["inspected_count"]
        )
        logger.info("==================== FLIGHT TRANSITION VALIDATION SUMMARY ====================")
        logger.info(f"Total Flights Inspected Across All Sections: {total_inspected}")
        logger.info(f"Ongoing Flights (Has ONBL, No OFBL): {ongoing_summary['passed_count']}/{ongoing_summary['inspected_count']}")
        logger.info(f"Incoming Flights (No ONBL, No OFBL): {incoming_summary['passed_count']}/{incoming_summary['inspected_count']}")
        logger.info(f"Departed Flights (Has ONBL, Has OFBL): {departed_summary['passed_count']}/{departed_summary['inspected_count']}")
        logger.info("All flight block-time transition and section placement rules verified successfully.")
