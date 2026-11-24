# Author : Tilak Badsheshi
# Created Date : 2026-11-16
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

import pytest
import allure
from pages.List_View.ListView_Ongoing_ActivityGantView_Page import ListView_Ongoing_ActivityGantView_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_listview_ongoing_activity_gant_view(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify that the Gantt View displays planned and actual activities, progress, and delays accurately.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Ensure Ongoing section is active and flights are loaded.
    4. Step 3: Enable the Gantt View toggle button.
    5. Step 4: Expand flight card to reveal the embedded Gantt chart.
    6. Step 5: Validate all activity groups and check planned vs actual timing bars.
    """
    logger.info("Starting List View Ongoing Section Gantt View Activities Validation Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    gantt_page = ListView_Ongoing_ActivityGantView_Page(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            gantt_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Make sure Ongoing section is loaded
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Ongoing Section is Active and Flights are Loaded"):
        total_flights = gantt_page.ensure_ongoing_section_loaded()
        with allure.step(f"2.1: Check Ongoing tab is active with flight cards displayed"):
            assert total_flights > 0, "No flight cards loaded in Ongoing section."
        allure.attach(
            f"Active Section: Ongoing\nTotal Flight Cards Loaded: {total_flights}",
            name="Ongoing_Section_Status",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Ongoing section active with {total_flights} flight cards")

    # -------------------------------------------------------------------------
    # Step 3: Turn on the Gantt View switch
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Enable Gantt View Toggle in List View"):
        with allure.step("3.1: Locate Gantt View switch and turn toggle ON"):
            toggle_enabled = gantt_page.enable_gantt_view_toggle()
        with allure.step("3.2: Verify that Gantt View toggle state is active"):
            assert toggle_enabled, "Failed to enable Gantt View toggle."
        allure.attach(
            "Gantt View toggle switch is turned ON.",
            name="Gantt_Toggle_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 4: Expand a flight card to see the Gantt chart
    # -------------------------------------------------------------------------
    with allure.step("Step 4: Select Flight Card to Reveal Gantt Chart"):
        with allure.step("4.1: Click flight card and open Gantt view"):
            flight_number = gantt_page.expand_flight_card_gantt(card_index=0)
        with allure.step(f"4.2: Verify flight card is expanded for Flight"):
            assert flight_number, "Failed to retrieve flight number from expanded card."
        allure.attach(
            f"Expanded Flight: {flight_number}\nStatus: Gantt chart container expanded.",
            name=f"{flight_number}_Expanded_Card",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Gantt View chart expanded for flight: '{flight_number}'")

    # -------------------------------------------------------------------------
    # Step 5: Check all activity groups and their planned vs actual times
    # -------------------------------------------------------------------------
    with allure.step(f"Step 5: Validate Planned & Actual Gantt Activities for Flight"):
        with allure.step("5.1: Collect and inspect all available activity groups and activity items"):
            validation_summary = gantt_page.validate_gantt_activities_all_groups()

        total_groups = validation_summary["total_groups"]
        total_activities = validation_summary["total_activities"]
        total_planned = validation_summary["total_with_planned"]
        total_actual = validation_summary["total_with_actual"]
        group_names = validation_summary["group_names"]

        with allure.step(f"5.2: Verify activity groups were found"):
            assert total_groups > 0, "No activity groups were found in Gantt View."

        with allure.step(f"5.3: Verify activities exist across groups"):
            assert total_activities > 0, "No activities were found across any activity group."

        with allure.step(f"5.4: Verify planned timing bars are displayed for activities"):
            assert total_planned > 0, "No activities had planned timing bars rendered."

        allure.attach(
            f"Target Flight: {flight_number}\n"
            f"Total Activity Groups Found: {total_groups}\n"
            f"Group Names: {', '.join(group_names)}\n"
            f"Total Activities Inspected: {total_activities}\n"
            f"Activities with Planned Times: {total_planned}\n"
            f"Activities with Actual Times: {total_actual}\n"
            f"Status: Planned and actual activity bars validated successfully.",
            name="Gantt_Validation_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )

        logger.info("==================== GANTT VIEW VALIDATION SUMMARY ====================")
        logger.info(f"Target Flight: {flight_number}")
        logger.info(f"Total Activity Groups Verified: {total_groups}")
        logger.info(f"Group Names: {group_names}")
        logger.info(f"Total Activities Inspected: {total_activities}")
        logger.info(f"Activities with Planned Times: {total_planned}")
        logger.info(f"Activities with Actual Times: {total_actual}")

        # Per group details
        for grp_name, acts in validation_summary["details"].items():
            logger.info(f"--- Group: '{grp_name}' ({len(acts)} activities) ---")
            for a in acts:
                planned_str = (
                    f"Start={a['planned']['start']}, End={a['planned']['end']}, Dur={a['planned']['duration']}"
                    if a['planned']['present']
                    else "Not Present"
                )
                actual_str = (
                    f"Start={a['actual']['start']}, OnTime={a['actual']['is_ontime']}, Delay={a['actual']['delay']}"
                    if a['actual']['present']
                    else "Not Present"
                )
                logger.info(f"  Activity: '{a['activity_name']}' | Planned: [{planned_str}] | Actual: [{actual_str}]")

    logger.info("List View Ongoing Section Gantt View Activities Validation Test completed successfully")
