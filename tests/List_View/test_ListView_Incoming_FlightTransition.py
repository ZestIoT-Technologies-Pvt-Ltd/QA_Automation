# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

import pytest
import allure
from pages.List_View.ListView_Incoming_FlightTransition_Pages import ListView_Incoming_FlightTransition_Pages
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_listview_incoming_flight_transition(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify that flights are placed into the correct section based on their On-Block (ONBL) and Off-Block (OFBL) times.

    Lifecycle Rules:
    1. Ongoing Section: Flights with On-Block time (ONBL) and WITHOUT Off-Block time (OFBL).
    2. Incoming Section: Flights with NO On-Block time and NO Off-Block time.
    3. Departed Section: Flights with BOTH On-Block time (ONBL) and Off-Block time (OFBL).

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Validate Ongoing section flights (Has ONBL, NO OFBL).
    4. Step 3: Validate Incoming section flights (NO ONBL, NO OFBL).
    5. Step 4: Validate Departed section flights (Has BOTH ONBL and OFBL).
    6. Step 5: Verify overall results across all sections.
    """
    logger.info("Starting Flights List View Section Transition & Block-Time Rules Validation Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    transition_page = ListView_Incoming_FlightTransition_Pages(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            transition_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Validate Ongoing Section (Has On-Block time, NO Off-Block time)
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Validate Ongoing Section Flights"):
        logger.info("--- Validating Ongoing Section Flights ---")
        with allure.step("2.1: Inspect flight cards in Ongoing section for ONBL and OFBL timings"):
            ongoing_summary = transition_page.validate_section_flights("Ongoing", max_flights=15)

        logger.info(
            f"Ongoing Summary: Inspected={ongoing_summary['inspected_count']}, "
            f"Passed={ongoing_summary['passed_count']}, Failed={ongoing_summary['failed_count']}"
        )

        with allure.step(f"2.2: Verify Ongoing flight cards are loaded"):
            assert ongoing_summary["total_cards"] > 0, (
                "No flight cards loaded in the Ongoing section."
            )

        # with allure.step("2.3: Assert zero block-time rule violations in Ongoing section"):
            assert ongoing_summary["failed_count"] == 0, (
                f"Ongoing section block-time violations detected in {ongoing_summary['failed_count']} flights: "
                f"{[f['flight_number'] + ' -> ' + f['reason'] for f in ongoing_summary['failed_cards']]}"
            )

        allure.attach(
            f"Section: Ongoing\n"
            f"Rule: Must have On-Block (ONBL) time and NO Off-Block (OFBL) time\n"
            f"Total Flights Loaded: {ongoing_summary['total_cards']}\n"
            f"Flights Inspected: {ongoing_summary['inspected_count']}\n"
            f"Passed: {ongoing_summary['passed_count']}\n"
            f"Failed: {ongoing_summary['failed_count']}\n"
            f"Status: All inspected ongoing flights satisfy the ONBL/OFBL rule.",
            name="Ongoing_Section_Validation",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 3: Validate Incoming Section (NO On-Block time, NO Off-Block time)
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Validate Incoming Section Flights"):
        logger.info("--- Validating Incoming Section Flights ---")
        with allure.step("3.1: Switch to Incoming section and inspect flight cards for ONBL and OFBL timings"):
            incoming_summary = transition_page.validate_section_flights("Incoming", max_flights=10)

        logger.info(
            f"Incoming Summary: Inspected={incoming_summary['inspected_count']}, "
            f"Passed={incoming_summary['passed_count']}, Failed={incoming_summary['failed_count']}"
        )

        #with allure.step("3.2: Assert zero block-time rule violations in Incoming section"):
        if incoming_summary["inspected_count"] > 0:
            assert incoming_summary["failed_count"] == 0, (
                f"Incoming section block-time violations detected in {incoming_summary['failed_count']} flights: "
                f"{[f['flight_number'] + ' -> ' + f['reason'] for f in incoming_summary['failed_cards']]}"
            )
        else:
            logger.info("Incoming section currently has 0 flights loaded; rule check bypassed.")

        allure.attach(
            f"Section: Incoming\n"
            f"Rule: Must have NO On-Block (ONBL) time and NO Off-Block (OFBL) time\n"
            f"Total Flights Loaded: {incoming_summary['total_cards']}\n"
            f"Flights Inspected: {incoming_summary['inspected_count']}\n"
            f"Passed: {incoming_summary['passed_count']}\n"
            f"Failed: {incoming_summary['failed_count']}\n"
            f"Status: All inspected incoming flights satisfy the rule.",
            name="Incoming_Section_Validation",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 4: Validate Departed Section (Has BOTH On-Block and Off-Block times)
    # -------------------------------------------------------------------------
    with allure.step("Step 4: Validate Departed Section Flights"):
        logger.info("--- Validating Departed Section Flights ---")
        with allure.step("4.1: Switch to Departed section and inspect flight cards for ONBL and OFBL timings"):
            departed_summary = transition_page.validate_section_flights("Departed", max_flights=10)

        logger.info(
            f"Departed Summary: Inspected={departed_summary['inspected_count']}, "
            f"Passed={departed_summary['passed_count']}, Failed={departed_summary['failed_count']}"
        )

        #with allure.step("4.2: Assert zero block-time rule violations in Departed section"):
        if departed_summary["inspected_count"] > 0:
            assert departed_summary["failed_count"] == 0, (
                f"Departed section block-time violations detected in {departed_summary['failed_count']} flights: "
                f"{[f['flight_number'] + ' -> ' + f['reason'] for f in departed_summary['failed_cards']]}"
            )
        else:
            logger.info("Departed section currently has 0 flights loaded; rule check bypassed.")

        allure.attach(
            f"Section: Departed\n"
            f"Rule: Must have BOTH On-Block (ONBL) time and Off-Block (OFBL) time\n"
            f"Total Flights Loaded: {departed_summary['total_cards']}\n"
            f"Flights Inspected: {departed_summary['inspected_count']}\n"
            f"Passed: {departed_summary['passed_count']}\n"
            f"Failed: {departed_summary['failed_count']}\n"
            f"Status: All inspected departed flights satisfy the rule.",
            name="Departed_Section_Validation",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 5: Overall Verification & Summary Logging
    # -------------------------------------------------------------------------
    # with allure.step("Step 5: Verify Overall Flight Transition Rules Across All Sections"):
    #     total_inspected = (
    #         ongoing_summary["inspected_count"]
    #         + incoming_summary["inspected_count"]
    #         + departed_summary["inspected_count"]
    #     )
    #     total_passed = (
    #         ongoing_summary["passed_count"]
    #         + incoming_summary["passed_count"]
    #         + departed_summary["passed_count"]
    #     )

    #     with allure.step(f"5.1: Check overall passing flights ({total_passed}/{total_inspected} flights passed)"):
    #         assert (ongoing_summary["failed_count"] + incoming_summary["failed_count"] + departed_summary["failed_count"]) == 0

    #     allure.attach(
    #         f"Total Flights Inspected Across All Sections: {total_inspected}\n"
    #         f"Ongoing Section Passed: {ongoing_summary['passed_count']}/{ongoing_summary['inspected_count']}\n"
    #         f"Incoming Section Passed: {incoming_summary['passed_count']}/{incoming_summary['inspected_count']}\n"
    #         f"Departed Section Passed: {departed_summary['passed_count']}/{departed_summary['inspected_count']}\n"
    #         f"Overall Status: All section placement and transition lifecycle rules verified successfully.",
    #         name="Overall_Transition_Summary",
    #         attachment_type=allure.attachment_type.TEXT,
    #     )

        logger.info("==================== FLIGHT TRANSITION VALIDATION SUMMARY ====================")
        #logger.info(f"Total Flights Inspected Across All Sections: {total_inspected}")
        logger.info(f"Ongoing Flights (Has ONBL, No OFBL): {ongoing_summary['passed_count']}/{ongoing_summary['inspected_count']}")
        logger.info(f"Incoming Flights (No ONBL, No OFBL): {incoming_summary['passed_count']}/{incoming_summary['inspected_count']}")
        logger.info(f"Departed Flights (Has ONBL, Has OFBL): {departed_summary['passed_count']}/{departed_summary['inspected_count']}")
        logger.info("All flight block-time transition and section placement rules verified successfully.")
