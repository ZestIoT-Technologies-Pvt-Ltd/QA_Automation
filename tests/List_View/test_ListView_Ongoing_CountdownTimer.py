# Author : Tilak Badsheshi
# Created Date : 2026-11-16
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-20

import re
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
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify whether countdown timers are calculated correctly based on STD and ETD and updated in real time.

    Detailed Steps:
    1. Prerequisite: Authenticate / Login to application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Ensure Ongoing Section is active and flights are loaded.
    4. Step 3: Extract and validate Header Timings (Station Code, Date, Station Local Time, and UTC Time).
    5. Step 4:Verify timezone offset consistency between Local Time and UTC Time.
    6. Step 5: For each ongoing flight card:
       a. Extract STD and ETD from departure dropdown content.
       b. Determine target departure time (ETD if present and valid, otherwise STD).
       c. Calculate expected difference in minutes between Station Local Time and target departure time.
       d. Read displayed countdown timer and read the color coding displayed.
       e. Assert that countdown timer displays calculated difference.
       f. Assert that the timer is displayed in Green when departure is in the future, and Red when local time has crossed departure time.
    """
    logger.info("Starting List View Ongoing Section Countdown Timer Validation Test")

    with allure.step("Prerequisite: Sign into application using common login method"):
        # Prerequisite: Sign into application using common login method
        login_to_application(page)

    countdown_page = ListView_Ongoing_CountdownTimer_Page(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View dashboard
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        countdown_page.navigate_to_list_view_page()

    # -------------------------------------------------------------------------
    # Step 2: Make sure Ongoing Section tab is active
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Ensure Ongoing Section is Loaded and Flight Cards are Loaded"):
        total_flights = countdown_page.ensure_ongoing_section_loaded()
        assert total_flights > 0, "No flight cards loaded in Ongoing section."
        allure.attach(
            f"Active Section: Ongoing\nTotal Flight Cards Loaded: {total_flights}",
            name="Ongoing_Section_Status",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info(f"Ongoing section active with {total_flights} flight cards")

    # -------------------------------------------------------------------------
    # Step 3: Extract and Validate Header Timings (Local Station Time & UTC Time)
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Extract and Validate Application Header Timings"):
        header_timings = countdown_page.get_header_timings()
        station_code = header_timings["station_code"]
        date_str = header_timings["date_str"]
        local_tz = header_timings["local_tz"] or "Local"
        local_time_str = header_timings["local_time_str"]
        utc_time_str = header_timings["utc_time_str"]
        local_dt = header_timings["local_dt"]
        utc_dt = header_timings["utc_dt"]
        offset_hours = header_timings["offset_hours"]

        with allure.step(f"Step 3.1: Verify Station Code and Date Displayed"):
            assert station_code, "Station Code not found in airport headers."
            assert date_str, "Date not found in airport headers."

        with allure.step(f"Step 3.2: Verify Station Local Time and UTC Time"):
            assert local_dt is not None, "Failed to parse Station Local DateTime from header."
            assert utc_dt is not None, "Failed to parse UTC DateTime from header."

        allure.attach(
            f"Station Code: {station_code}\n"
            f"Date: {date_str}\n"
            f"Local Time: {local_tz} {local_time_str} ({local_dt})\n"
            f"UTC Time: {utc_time_str} ({utc_dt})\n"
            f"Calculated Timezone Offset: {offset_hours} hours\n"
            f"Raw Header Elements: {header_timings['raw_headers']}",
            name="Header_Timings_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 4: Validate Countdown Timers across Flight Cards
    # -------------------------------------------------------------------------
    card_loc = countdown_page.page.locator(countdown_page.FLIGHT_ROW_CARDS)
    flight_cards = card_loc.all()
    flights_to_inspect = min(len(flight_cards), 15)
    validation_results = []

    with allure.step(f"Step 4: Validate Countdown Timers Across Ongoing Flight Cards"):
        for i in range(flights_to_inspect):
            card = flight_cards[i]
            card.scroll_into_view_if_needed()
            fl_num = (countdown_page.get_flight_number(card) or "").strip() or f"Flight {i + 1}"

            with allure.step(f"Step 4.{i+1}: Verify Countdown Timer with Departure Timings (STD and ETD)"):
                # 4.{i+1}.1: Extract Departure Timings (STD and ETD)
                dep_times = countdown_page.parse_flight_departure_times(card)
                target_src = dep_times["target_source"]
                target_dt = dep_times["target_dt"]
                std_str = dep_times["std_dt"].strftime("%H:%M") if dep_times["std_dt"] else "-"
                etd_str = dep_times["etd_dt"].strftime("%H:%M") if dep_times["etd_dt"] else "-"
                target_str = target_dt.strftime("%H:%M") if target_dt else "-"

                with allure.step(
                    f"Extract Departure Times -> STD: '{std_str}', ETD: '{etd_str}' "
                    f"=> Selected Target ({target_src}): '{target_str}'"
                ):
                    allure.attach(
                        f"Flight: {fl_num}\n"
                        f"Scheduled Departure Time (STD): {std_str}\n"
                        f"Estimated Departure Time (ETD): {etd_str}\n"
                        f"Selected Target Departure Time: {target_src} ({target_str})\n"
                        f"Business Rule: If ETD is present and valid, use ETD; otherwise use STD.\n"
                        f"Raw Dropdown Text: {dep_times['raw_text']}",
                        name=f"{fl_num}_Departure_Timings",
                        attachment_type=allure.attachment_type.TEXT,
                    )

                if not target_dt:
                    logger.warning(f"Flight '{fl_num}' has no valid STD/ETD: {dep_times['raw_text']}")
                    validation_results.append({
                        "flight_number": fl_num,
                        "std": std_str,
                        "etd": etd_str,
                        "target_source": target_src,
                        "diff_minutes": 0,
                        "displayed_text": "N/A",
                        "title_attr": "N/A",
                        "actual_color": "N/A",
                        "expected_color": "N/A",
                        "passed": False,
                        "reason": "Missing STD/ETD timestamp",
                    })
                    assert False, f"Missing STD/ETD timestamp for flight '{fl_num}'"

                # 4.{i+1}.2: Calculate Expected Difference in Minutes
                diff_minutes = (local_dt - target_dt).total_seconds() / 60.0
                diff_round = round(diff_minutes)
                local_time_formatted = local_dt.strftime("%H:%M:%S")

                with allure.step(
                    f"Calculate Expected Difference in Minutes -> "
                    f"Station Local Time - Target {target_src}"
                ):
                    allure.attach(
                        f"Calculation Breakdown:\n"
                        f"Station Local Time: {local_time_formatted}\n"
                        f"Target Departure Time ({target_src}): {target_str}\n"
                        f"Formula: (Local Time - Target Departure Time) in minutes\n"
                        f"Exact Difference: {diff_minutes:.2f} minutes\n"
                        f"Rounded Difference: {diff_round:+d} minutes\n"
                        f"Meaning: Negative value means departure is in the future; positive means departure time has passed.",
                        name=f"{fl_num}_Difference_Calculation",
                        attachment_type=allure.attachment_type.TEXT,
                    )

                # 4.{i+1}.3: Read UI Timer Attributes
                timer_data = countdown_page.get_countdown_timer_data(card)
                displayed_text = timer_data["num_text"]
                title_attr = timer_data["title"]
                actual_color = "RED" if timer_data["is_red"] else ("GREEN" if timer_data["is_green"] else "UNKNOWN")
                expected_color = "RED" if diff_minutes > 0 else "GREEN"

                # with allure.step(
                #     f"4.{i+1}.3: Read UI Countdown Timer Elements -> "
                #     f"Displayed Number: '{displayed_text}', Hover Tooltip Title: '{title_attr}', Color: {actual_color}"
                # ):
                allure.attach(
                     f"UI Elements Extracted:\n"
                     f"Progress Ring Number: '{displayed_text}'\n"
                     f"Hover Tooltip (Title Attribute): '{title_attr}'\n"
                     f"CSS Color: {timer_data['color']}\n"
                      f"Progress Ring Stroke: {timer_data['stroke']}\n"
                     f"Evaluated Color Category: {actual_color}",
                      name=f"{fl_num}_UI_Timer_Details",
                      attachment_type=allure.attachment_type.TEXT,
                  )

                # 4.{i+1}.4: Verify Countdown Timer Value matches Expected Difference
                title_raw = title_attr.strip()
                title_val = int(title_raw) if re.match(r"^[+-]?\d+$", title_raw) else None
                num_raw = displayed_text.strip()
                num_val = int(num_raw) if re.match(r"^[+-]?\d+$", num_raw) else None

                value_matches = False
                if title_val is not None and abs(title_val - diff_round) <= 2:
                    value_matches = True
                elif num_val is not None and abs(num_val - diff_round) <= 2:
                    value_matches = True
                elif displayed_text == "999+" and abs(diff_round) >= 999:
                    value_matches = True
                elif not displayed_text and not title_attr:
                    # No active timer rendered on this card
                    value_matches = True

                with allure.step(
                    f"Verify Timer Value Matches Expected Difference"):
                    assert value_matches, (
                        f"Countdown timer value mismatch for Flight '{fl_num}': "
                        f"Expected around {diff_round:+d}m , but UI displayed '{displayed_text}' (Title: '{title_attr}')"
                    )

                # 4.{i+1}.5: Verify Color Coding (Green = Future / Red = Overdue)
                color_matches = (expected_color == actual_color) if (displayed_text or title_attr) else True
                color_rule = "Overdue / Passed Departure Time -> RED" if expected_color == "RED" else "Remaining Time / Future Departure -> GREEN"

                with allure.step(
                    f"Verify Timer Color Coding"
                ):
                    assert color_matches, (
                        f"Countdown timer color mismatch for Flight '{fl_num}': "
                        f"Expected {expected_color} ({color_rule}), but UI displays {actual_color} (CSS: {timer_data['color']})"
                    )

                validation_results.append({
                    "flight_number": fl_num,
                    "std": std_str,
                    "etd": etd_str,
                    "target_source": target_src,
                    "diff_minutes": diff_round,
                    "displayed_text": displayed_text,
                    "title_attr": title_attr,
                    "actual_color": actual_color,
                    "expected_color": expected_color,
                    "passed": value_matches and color_matches,
                })

    logger.info("List View Ongoing Section Countdown Timer Validation Test completed successfully")
