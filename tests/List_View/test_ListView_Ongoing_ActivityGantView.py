# Author : Tilak Badsheshi
# Created Date : 2026-11-16
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-16

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
    ==============  INTRODUCTION ================
    Test Scenario: Verify whether the Gantt View represents planned and actual activities, dependencies, progress and delays accurately.

    Steps:
    1. Prerequisite: Authenticate / Login to application using common login method.
    2. Navigate to Flights List View dashboard.
    3. Ensure Ongoing Section is active and flight cards are loaded.
    4. Locate and enable the Gantt View toggle in the List View toolbar.
    5. Select a flight card to expand the embedded Gantt chart view.
    6. Discover all available Activity Groups (e.g. Aircraft Recipients, Technical Equipment, Arrival Events, Departure Events, Departure Readiness).
    7. Sequentially navigate through all Activity Groups:
       a. Verify that activities are correctly displayed for each activity group.
       b. Verify planned time (Start, End, Duration) is displayed on planned activity bars.
       c. Check whether actual time (Start, End, Delay) is displayed on actual activity bars.
       d. Verify progress, on-time (Green) and delay (Red) representations.
    8. Assert validation results across all activity groups.
    """
    logger.info("Starting List View Ongoing Section Gantt View Activities Validation Test")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    gantt_page = ListView_Ongoing_ActivityGantView_Page(page, None)

    # Step 1: Navigate to Flights List View Dashboard
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        gantt_page.navigate_to_list_view_page()

    # Step 2: Ensure Ongoing Section is active and flights are loaded
    with allure.step("Step 2: Ensure Ongoing Section is Active and Flights are Loaded"):
        total_flights = gantt_page.ensure_ongoing_section_loaded()
        assert total_flights > 0, "No flight cards loaded in Ongoing section."
        logger.info(f"Ongoing section active with {total_flights} flight cards")

    # Step 3: Enable Gantt View toggle in List View
    with allure.step("Step 3: Enable Gantt View Toggle in List View"):
        toggle_enabled = gantt_page.enable_gantt_view_toggle()
        assert toggle_enabled, "Failed to enable Gantt View toggle."

    # Step 4: Select / Expand Flight Card to reveal Gantt Chart
    with allure.step("Step 4: Select Flight Card to Reveal Gantt Chart"):
        flight_number = gantt_page.expand_flight_card_gantt(card_index=0)
        logger.info(f"Gantt View chart expanded for flight: '{flight_number}'")

    # Step 5: Validate All Activity Groups and Planned/Actual Activities
    with allure.step(f"Step 5: Validate Planned & Actual Gantt Activities for Flight '{flight_number}'"):
        validation_summary = gantt_page.validate_gantt_activities_all_groups()

        # Assertions
        assert validation_summary["total_groups"] > 0, "No activity groups were found in Gantt View."
        assert validation_summary["total_activities"] > 0, "No activities were found across any activity group."
        assert validation_summary["total_with_planned"] > 0, "No activities had planned timing bars rendered."

        logger.info("==================== GANTT VIEW VALIDATION SUMMARY ====================")
        logger.info(f"Target Flight: {flight_number}")
        logger.info(f"Total Activity Groups Verified: {validation_summary['total_groups']}")
        logger.info(f"Group Names: {validation_summary['group_names']}")
        logger.info(f"Total Activities Inspected: {validation_summary['total_activities']}")
        logger.info(f"Activities with Planned Times: {validation_summary['total_with_planned']}")
        logger.info(f"Activities with Actual Times: {validation_summary['total_with_actual']}")

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
