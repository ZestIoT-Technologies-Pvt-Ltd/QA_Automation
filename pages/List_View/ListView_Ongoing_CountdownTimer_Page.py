# Author : Tilak Badsheshi
# Created Date : 2026-11-16
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-16

"""
==============  INTRODUCTION ================
Page Object / Component: ListView_Ongoing_CountdownTimer_Page
Description: Page Object Model for validating Flight Countdown Timers and Header Timings
             (Station Local Time and UTC Time) in the Ongoing section on Flights List View.

Scenario & Workflow Capabilities:
1. Navigation: Route through navigation menu to Flights List View dashboard.
2. Section Switching: Switch to Ongoing section and ensure flight cards are loaded (sync fallback).
3. Header Timing Extraction & Validation:
   - Extract Station Code (e.g. 'DXB').
   - Extract Date (e.g. '16 Nov').
   - Extract Station Local Time with timezone (e.g. 'GST : 09:50:00').
   - Extract UTC Time (e.g. 'UTC : 05:50:00').
   - Validate time consistency and timezone offset between Local Time and UTC Time.
4. Departure Times Parsing (STD & ETD):
   - Parse STD and ETD from flight card departure dropdown.
   - Priority rule: If both STD and ETD are present -> consider ETD; if ETD is not present -> consider STD.
5. Countdown Timer Calculation & Color Validation:
   - Calculate expected difference in minutes between Station Local Time and Target Departure Time (ETD/STD).
   - Verify countdown timer display / title value matches expected difference within +/- 2 minutes tolerance.
   - Validate color styling:
     * Green (rgb(74, 187, 34)) when departure time is in the future.
     * Red (rgb(235, 33, 33)) when local time has crossed departure time (overdue).
6. Real-Time Dynamic Clock Verification:
   - Verify that Station Local Time and UTC Time tick dynamically in real time without page reload.
"""

import re
from datetime import datetime
import pytest
import allure
from playwright.sync_api import expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Ongoing_CountdownTimer_Page(BasePage):
    """
    Page Object dedicated to Header Timings (Local & UTC) and Flight Card Countdown Timer
    validations in the Ongoing section of the Flights List View.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    LIST_VIEW = "//div[@role='button']//span[normalize-space()='Flights'] | //span[normalize-space()='Flights']"

    SECTIONS = [
        {"name": "Ongoing", "tab": "//div[contains(text(),'Ongoing')]"},
        {"name": "Incoming", "tab": "//div[contains(text(),'Incoming')]"},
        {"name": "Departed", "tab": "//div[contains(text(),'Departed')]"},
    ]

    HEADER_AIRPORT_HEADERS = ".airport-headers"
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    SYNC_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"

    FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = (
        "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
        "//div[contains(@class,'flightno-col')] | "
        "//p[@mattooltip='Flight Arrival Departure Numbers']"
    )
    DEPARTURE_TIME_COL = ".departure-time-col"
    DEPARTURE_DROPDOWN_CONTENT = ".departure-time-col .dropdown-content"
    COUNTDOWN_TIMER_CONTAINER = ".countdown-col-incoming"
    COUNTDOWN_TIMER_NUMBER = ".progress-ring__number"
    PROGRESS_RING_CIRCLE = ".progress-ring__circle"

    # Known color values for countdown timer
    COLOR_RED_RGB = (235, 33, 33)
    COLOR_GREEN_RGB = (74, 187, 34)

    @allure.step("Navigate to Flights List View Dashboard")
    def navigate_to_list_view_page(self):
        """Navigates to the Flights List View dashboard via the main navigation menu."""
        logger.info("Navigating to Flights List View dashboard")
        self.page.wait_for_timeout(2000)

        menu = self.page.locator(self.MENU).first
        expect(menu).to_be_visible(timeout=20000)
        menu.hover()
        self.page.wait_for_timeout(500)

        list_view = self.page.locator(self.LIST_VIEW).first
        if not list_view.is_visible():
            logger.info("List View menu item not visible after hover; clicking hamburger menu")
            menu.click()
            self.page.wait_for_timeout(1000)

        expect(list_view).to_be_visible(timeout=15000)
        list_view.click()
        self.page.wait_for_timeout(2000)

        # Move mouse to dismiss open navigation overlay
        self.page.mouse.move(600, 500)
        self.page.wait_for_timeout(1500)

        # Wait for any spinner / loader container to clear
        try:
            self.page.locator(".loader-container, .spinner").wait_for(state="detached", timeout=15000)
        except Exception:
            pass

        logger.info("Successfully navigated to Flights List View dashboard")

    @allure.step("Switch to Ongoing Section and Ensure Flight Cards are Loaded")
    def ensure_ongoing_section_loaded(self) -> int:
        """
        Switches to the Ongoing section tab, verifies flights are loaded,
        and clicks the Refresh Flight sync icon if needed. Returns total flight cards count.
        """
        logger.info("Activating Ongoing section tab")
        ongoing_tab = self.page.locator(self.SECTIONS[0]["tab"]).first
        expect(ongoing_tab).to_be_visible(timeout=15000)
        ongoing_tab.click(force=True)
        self.page.wait_for_timeout(2000)

        card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
        try:
            card_loc.first.wait_for(state="visible", timeout=8000)
        except Exception:
            sync_icon = self.page.locator(self.SYNC_ICON).first
            if sync_icon.count() > 0 and sync_icon.is_visible():
                logger.info("Flight cards not immediately visible. Triggering Refresh Flight sync icon...")
                sync_icon.click()
                self.page.wait_for_timeout(4000)
            card_loc.first.wait_for(state="visible", timeout=15000)

        total_cards = card_loc.count()
        logger.info(f"Ongoing section active with {total_cards} flight cards loaded")
        return total_cards

    @allure.step("Extract and Validate Header Timings (Station Local Time and UTC Time)")
    def get_header_timings(self) -> dict:
        """
        Extracts station code, date, local station time, timezone label, and UTC time from
        header elements (.airport-headers).
        Example header elements:
          - 'DXB'
          - '16 Nov'
          - 'GST : 09:42:23'
          - 'UTC : 05:42:23'
        Returns a dictionary with parsed strings, datetime objects, and timezone offset.
        """
        headers = self.page.locator(self.HEADER_AIRPORT_HEADERS).all()
        station_code = None
        date_str = None
        local_time_str = None
        local_tz_str = None
        utc_time_str = None

        raw_header_texts = []
        for h in headers:
            text = h.inner_text().strip()
            if not text:
                continue
            raw_header_texts.append(text)

            if re.match(r"^[A-Z]{3}$", text):
                station_code = text
            elif re.match(r"^\d{1,2}\s+[A-Za-z]{3}$", text):
                date_str = text
            elif text.startswith("UTC"):
                m = re.search(r"UTC\s*:\s*(\d{1,2}:\d{2}:\d{2})", text)
                if m:
                    utc_time_str = m.group(1)
            elif ":" in text:
                m = re.search(r"([A-Za-z]{3,4})\s*:\s*(\d{1,2}:\d{2}:\d{2})", text)
                if m:
                    local_tz_str = m.group(1)
                    local_time_str = m.group(2)
                else:
                    m2 = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", text)
                    if m2:
                        local_time_str = m2.group(1)

        current_year = datetime.now().year
        local_dt = None
        if date_str and local_time_str:
            parts = local_time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) > 2 else 0
            dt_base = datetime.strptime(f"{date_str} {current_year}", "%d %b %Y")
            local_dt = dt_base.replace(hour=hour, minute=minute, second=second)

        utc_dt = None
        if date_str and utc_time_str:
            parts = utc_time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) > 2 else 0
            dt_base = datetime.strptime(f"{date_str} {current_year}", "%d %b %Y")
            utc_dt = dt_base.replace(hour=hour, minute=minute, second=second)

        # Calculate time offset between Station Local Time and UTC Time
        offset_hours = None
        if local_dt and utc_dt:
            offset_seconds = (local_dt - utc_dt).total_seconds()
            offset_hours = round(offset_seconds / 3600.0, 2)

        result = {
            "station_code": station_code,
            "date_str": date_str,
            "local_tz": local_tz_str,
            "local_time_str": local_time_str,
            "utc_time_str": utc_time_str,
            "local_dt": local_dt,
            "utc_dt": utc_dt,
            "offset_hours": offset_hours,
            "raw_headers": raw_header_texts,
        }

        logger.info(
            f"Header Timings: Station={station_code}, Date='{date_str}', "
            f"LocalTime={local_tz_str}:{local_time_str} ({local_dt}), "
            f"UTCTime={utc_time_str} ({utc_dt}), Offset={offset_hours} hrs"
        )
        return result

    @allure.step("Extract Departure Times (STD and ETD) for Flight Card")
    def parse_flight_departure_times(self, flight_card) -> dict:
        """
        Extracts STD and ETD from the departure time column dropdown content.
        Applies condition:
          - If both STD and ETD are present -> consider ETD.
          - If ETD is not present -> consider STD.
        """
        dep_content = flight_card.locator(self.DEPARTURE_DROPDOWN_CONTENT).first
        text = dep_content.inner_text() if dep_content.count() > 0 else ""
        text = text.replace("\xa0", " ").replace("&nbsp;", " ")

        std_dt = None
        etd_dt = None

        std_match = re.search(r"STD:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})", text)
        if std_match:
            try:
                std_dt = datetime.strptime(std_match.group(1), "%d/%m/%Y %H:%M")
            except Exception:
                pass

        etd_match = re.search(r"ETD:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})", text)
        if etd_match:
            try:
                etd_dt = datetime.strptime(etd_match.group(1), "%d/%m/%Y %H:%M")
            except Exception:
                pass

        # Rule: If ETD is present and valid, consider ETD; otherwise consider STD
        if etd_dt:
            target_dt = etd_dt
            target_source = "ETD"
        else:
            target_dt = std_dt
            target_source = "STD"

        return {
            "std_dt": std_dt,
            "etd_dt": etd_dt,
            "target_dt": target_dt,
            "target_source": target_source,
            "raw_text": text.strip().replace("\n", " | "),
        }

    @allure.step("Extract Countdown Timer Display, Value, and Color")
    def get_countdown_timer_data(self, flight_card) -> dict:
        """
        Extracts countdown timer attributes:
          - title attribute (exact signed minute difference, e.g. '+2812', '-15')
          - displayed number (e.g. '+9', '-11', '999+')
          - CSS color of number and stroke color of circular progress ring
          - determines whether displayed in RED or GREEN
        """
        countdown_col = flight_card.locator(self.COUNTDOWN_TIMER_CONTAINER).first
        title = countdown_col.get_attribute("title") if countdown_col.count() > 0 else ""

        num_elem = flight_card.locator(self.COUNTDOWN_TIMER_NUMBER).first
        num_text = num_elem.inner_text().strip() if num_elem.count() > 0 else ""
        color = num_elem.evaluate("el => window.getComputedStyle(el).color") if num_elem.count() > 0 else ""

        circle_elem = flight_card.locator(self.PROGRESS_RING_CIRCLE).first
        stroke = circle_elem.evaluate("el => window.getComputedStyle(el).stroke") if circle_elem.count() > 0 else ""

        is_red = False
        is_green = False
        m = re.search(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if r > 180 and g < 100:
                is_red = True
            elif g > 130 and r < 130:
                is_green = True

        return {
            "title": title.strip() if title else "",
            "num_text": num_text,
            "color": color,
            "stroke": stroke,
            "is_red": is_red,
            "is_green": is_green,
        }

    @allure.step("Validate Countdown Timer Calculation & Color for Flight Card")
    def validate_countdown_timer_for_card(self, flight_card, local_dt: datetime) -> dict:
        """
        Validates countdown timer calculation and color against target departure time (ETD/STD) and local station time:
        1. Selects ETD if present, else STD.
        2. Expected time difference in minutes = (local_dt - target_dt).
        3. Color validation:
           - If local time crosses departure time (diff > 0): RED (overdue)
           - If departure time is in future (diff <= 0): GREEN (remaining time)
        4. Display value check within +/- 2 minutes tolerance.
        """
        try:
            flight_no = self.get_flight_number(flight_card)
        except Exception:
            flight_no = "Unknown Flight"

        times = self.parse_flight_departure_times(flight_card)
        timer = self.get_countdown_timer_data(flight_card)

        target_dt = times["target_dt"]
        if not target_dt:
            logger.warning(f"Flight '{flight_no}' has no valid STD/ETD: {times['raw_text']}")
            return {
                "flight_number": flight_no,
                "passed": False,
                "reason": "Missing STD/ETD timestamp",
                "details": times,
            }

        diff_minutes = (local_dt - target_dt).total_seconds() / 60.0
        diff_round = round(diff_minutes)

        # Color expectation:
        # If local time crossed target departure time -> RED (overdue/delayed)
        # If departure time is in the future -> GREEN (on schedule / remaining time)
        expected_color = "RED" if diff_minutes > 0 else "GREEN"
        actual_color = "RED" if timer["is_red"] else ("GREEN" if timer["is_green"] else "UNKNOWN")

        # If no countdown timer is rendered (flight departure is distant or turnaround not active yet)
        if not timer["num_text"] and not timer["title"]:
            logger.info(
                f"Flight '{flight_no}' has no active countdown timer rendered (departure is {diff_round}m away). Skipping card validation."
            )
            return {
                "flight_number": flight_no,
                "target_source": times["target_source"],
                "target_dt": target_dt,
                "local_dt": local_dt,
                "diff_minutes": diff_round,
                "displayed_text": "",
                "title_attr": "",
                "expected_color": expected_color,
                "actual_color": "NONE",
                "color_css": "",
                "value_matches": True,
                "color_matches": True,
                "passed": True,
                "skipped": True,
            }

        # Value comparison:
        # Timer may display exact value (+9, -11) or '999+' for large values with exact value in title attribute
        title_raw = timer["title"].strip()
        title_val = int(title_raw) if re.match(r"^[+-]?\d+$", title_raw) else None

        num_raw = timer["num_text"].strip()
        num_val = int(num_raw) if re.match(r"^[+-]?\d+$", num_raw) else None

        value_matches = False
        if title_val is not None and abs(title_val - diff_round) <= 2:
            value_matches = True
        elif num_val is not None and abs(num_val - diff_round) <= 2:
            value_matches = True
        elif timer["num_text"] == "999+" and abs(diff_round) >= 999:
            value_matches = True

        color_matches = (expected_color == actual_color)
        passed = value_matches and color_matches

        result = {
            "flight_number": flight_no,
            "target_source": times["target_source"],
            "target_dt": target_dt,
            "local_dt": local_dt,
            "diff_minutes": diff_round,
            "displayed_text": timer["num_text"],
            "title_attr": timer["title"],
            "expected_color": expected_color,
            "actual_color": actual_color,
            "color_css": timer["color"],
            "value_matches": value_matches,
            "color_matches": color_matches,
            "passed": passed,
        }

        log_level = logger.info if passed else logger.error
        log_level(
            f"Flight '{flight_no}' Countdown Validation -> Target={times['target_source']}({target_dt}), "
            f"LocalTime={local_dt.strftime('%H:%M:%S')}, Diff={diff_round}m, "
            f"TimerText='{timer['num_text']}'(Title='{timer['title']}'), "
            f"ColorExp={expected_color}, ColorAct={actual_color} => {'PASSED' if passed else 'FAILED'}"
        )

        return result

    @allure.step("Verify Real-Time Dynamic Updates for Local and UTC Clocks")
    def validate_realtime_clock_updates(self, wait_seconds: int = 4) -> dict:
        """
        Validates that both Station Local Time and UTC Time tick dynamically in real time
        without needing a page reload.
        """
        logger.info(f"Checking real-time clock updates across a {wait_seconds}s interval...")
        t0 = self.get_header_timings()
        self.page.wait_for_timeout(wait_seconds * 1000)
        t1 = self.get_header_timings()

        local_ticked = False
        utc_ticked = False

        if t0["local_dt"] and t1["local_dt"]:
            local_diff = (t1["local_dt"] - t0["local_dt"]).total_seconds()
            local_ticked = (local_diff >= wait_seconds - 1)
            logger.info(
                f"Local clock ticked: T0={t0['local_time_str']} -> T1={t1['local_time_str']} (diff={local_diff}s)"
            )

        if t0["utc_dt"] and t1["utc_dt"]:
            utc_diff = (t1["utc_dt"] - t0["utc_dt"]).total_seconds()
            utc_ticked = (utc_diff >= wait_seconds - 1)
            logger.info(
                f"UTC clock ticked: T0={t0['utc_time_str']} -> T1={t1['utc_time_str']} (diff={utc_diff}s)"
            )

        return {
            "local_ticked": local_ticked,
            "utc_ticked": utc_ticked,
            "passed": local_ticked and utc_ticked,
        }
