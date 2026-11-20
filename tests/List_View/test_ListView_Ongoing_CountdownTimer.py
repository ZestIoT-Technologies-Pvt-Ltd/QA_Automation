# Author : Tilak Badsheshi
# Created Date : 2026-11-16
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-16

import pytest
import allure
from pages.List_View.ListView_Ongoing_CountdownTimer_Page import ListView_Ongoing_CountdownTimer_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_listview_ongoing_countdown_timer(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify whether countdown timers are calculated correctly based on STD and ETD and updated in real time.

    Steps:
    1. Prerequisite: Authenticate / Login to application using common login method.
    2. Navigate to Flights List View dashboard.
    3. Ensure Ongoing Section is active and flights are loaded.
    4. Extract and validate Header Timings (Station Code, Date, Station Local Time, and UTC Time).
       Verify timezone offset consistency between Local Time and UTC Time.
    5. For each ongoing flight card:
       a. Extract STD and ETD from departure dropdown content.
       b. Determine target departure time (ETD if present and valid, otherwise STD).
       c. Extract displayed countdown timer number, title attribute, and color styling.
       d. Calculate expected difference in minutes between Station Local Time and target departure time.
       e. Assert that countdown timer displays calculated difference within +/- 2 minutes tolerance.
       f. Assert that the timer is displayed in Green when departure is in the future, and Red when local time has crossed departure time.
    6. Verify real-time dynamic clock updates for both Local Time and UTC Time.
    """
    logger.info("Starting List View Ongoing Section Countdown Timer Validation Test")

    # Prerequisite: Sign into application using common login method
    login_to_application(page)

    countdown_page = ListView_Ongoing_CountdownTimer_Page(page, None)

    # Step 1: Navigate to Flights List View
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        countdown_page.navigate_to_list_view_page()

    # Step 2: Ensure Ongoing Section is active and flights are loaded
    with allure.step("Step 2: Ensure Ongoing Section is Active and Flights are Loaded"):
        total_flights = countdown_page.ensure_ongoing_section_loaded()
        assert total_flights > 0, "No flight cards loaded in Ongoing section."
        logger.info(f"Ongoing section active with {total_flights} flight cards")

    # Step 3: Extract and Validate Header Timings (Local Station Time & UTC Time)
    with allure.step("Step 3: Extract and Validate Header Timings (Local Station Time & UTC Time)"):
        header_timings = countdown_page.get_header_timings()
        logger.info(f"Header Timings: {header_timings}")

        station_code = header_timings["station_code"]
        local_dt = header_timings["local_dt"]
        utc_dt = header_timings["utc_dt"]
        offset_hours = header_timings["offset_hours"]

        assert local_dt is not None, "Failed to parse Station Local DateTime from application header."
        assert utc_dt is not None, "Failed to parse UTC DateTime from application header."

        logger.info(
            f"Station: '{station_code}', Local Time: {local_dt.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"UTC Time: {utc_dt.strftime('%Y-%m-%d %H:%M:%S')}, Offset: {offset_hours} hours"
        )

        # Validate timezone offset for DXB (Gulf Standard Time is UTC+4)
        if station_code == "DXB" and offset_hours is not None:
            assert abs(offset_hours - 4.0) <= 0.05, (
                f"Expected DXB (GST) time to be UTC+4, but calculated offset is {offset_hours} hours."
            )
            logger.info("Station Local Time vs UTC Time offset correctly validated as UTC+4 for DXB")

    # Step 4: Validate Countdown Timers for each flight card
    card_loc = countdown_page.page.locator(countdown_page.FLIGHT_ROW_CARDS)
    flight_cards = card_loc.all()
    flights_to_inspect = min(len(flight_cards), 15)

    validation_results = []
    with allure.step(f"Step 4: Validate Countdown Timers across {flights_to_inspect} Flight Cards"):
        for i in range(flights_to_inspect):
            card = flight_cards[i]
            card.scroll_into_view_if_needed()
            fl_num = countdown_page.get_flight_number(card)
            with allure.step(f"Step 4.{i+1}: Validate Countdown Timer for Flight '{fl_num}'"):
                res = countdown_page.validate_countdown_timer_for_card(card, local_dt)
                validation_results.append(res)

                # Assert individual card properties
                assert res.get("passed", False), (
                    f"Countdown timer validation failed for Flight '{res.get('flight_number')}': "
                    f"Target={res.get('target_source')}({res.get('target_dt')}), "
                    f"Diff={res.get('diff_minutes')}m, Displayed='{res.get('displayed_text')}' "
                    f"(Title='{res.get('title_attr')}'), ValueMatch={res.get('value_matches')}, "
                    f"ColorExp={res.get('expected_color')}, ColorAct={res.get('actual_color')}, "
                    f"ColorMatch={res.get('color_matches')}"
                )

    # Step 5: Verify Real-Time Dynamic Updates for Local and UTC Clocks
    with allure.step("Step 5: Verify Real-Time Dynamic Updates for Local and UTC Clocks"):
        clock_status = countdown_page.validate_realtime_clock_updates(wait_seconds=4)
        assert clock_status["local_ticked"], "Station Local Time is not ticking dynamically in real time."
        assert clock_status["utc_ticked"], "UTC Time is not ticking dynamically in real time."
        logger.info("Real-time dynamic ticking verified for both Station Local Time and UTC Time")

    logger.info("==================== COUNTDOWN TIMER EXECUTION SUMMARY ====================")
    for r in validation_results:
        logger.info(
            f"Flight: {r['flight_number']} | Target: {r['target_source']} ({r['target_dt']}) | "
            f"Diff: {r['diff_minutes']}m | Display: '{r['displayed_text']}' | "
            f"Color: {r['actual_color']} (Exp: {r['expected_color']}) => PASSED"
        )

    logger.info("List View Ongoing Section Countdown Timer Validation Test completed successfully")
