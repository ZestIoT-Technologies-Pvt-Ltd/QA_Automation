# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

"""
==============  INTRODUCTION ================
Page Object: ListView_Incoming_FlightTransition_Pages
Description: Page Object Model for validating flight presence and transition across List View
             sections (Incoming, Ongoing, Departed) based on On-Block (ONBL) and Off-Block (OFBL) timing rules.

Scenario & Workflow Capabilities:
1. Navigation: Route to Flights List View dashboard via side navigation menu.
2. Section Switching: Switch dynamically between Incoming, Ongoing, and Departed section tabs.
3. Timing Extraction:
   - Hover on Arrival Column to extract STA, ETA, and On-Block time (ONBL).
   - Hover on Departure Column to extract STD, ETD, and Off-Block time (OFBL).
4. Business Rule Validation:
   - Incoming Section: Flight has NO On-Block time and NO Off-Block time.
   - Ongoing Section:  Flight HAS On-Block time and NO Off-Block time.
   - Departed Section: Flight HAS BOTH On-Block time and Off-Block time.
5. Error Diagnostics & Element Highlighting:
   - On assertion or rule violation, automatically binds failing flight card to _last_failed_locator
     for prominent red border capture in failure screenshots.
"""

from __future__ import annotations

import re
import allure
from typing import Any, Dict, List, Optional
from playwright.sync_api import expect, Locator

from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Incoming_FlightTransition_Pages(BasePage):
    """
    Page Object dedicated to validating flight presence across Incoming, Ongoing,
    and Departed sections based on On-Block (ONBL) and Off-Block (OFBL) timing rules.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    LIST_VIEW = "//div[@role='button']//span[normalize-space()='Flights'] | //span[normalize-space()='Flights']"

    SECTIONS = {
        "Incoming": "//div[contains(text(),'Incoming')]",
        "Ongoing": "//div[contains(text(),'Ongoing')]",
        "Departed": "//div[contains(text(),'Departed')]",
        "Non Operational": "//div[contains(text(),'Non Operational')]",
    }

    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"
    SYNC_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"

    # Flight card metadata & time columns
    FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = (
        "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
        "//div[contains(@class,'flightno-col')] | "
        "//p[@mattooltip='Flight Arrival Departure Numbers']"
    )
    BAY_NUMBER = "//div[contains(@class,'bay-col')]"
    GATE_NUMBER = "//div[contains(@class,'gate-col')]"

    # Arrival time column & dropdown
    ARRIVAL_TIME_COL = "//div[contains(@class,'arrival-time-col')]"
    ARRIVAL_DROPDOWN_CONTENT = "//div[contains(@class,'arrival-time-col')]//div[contains(@class,'dropdown-content')]"
    ONBLOCK_PARAGRAPH = "//div[contains(@class,'arrival-time-col')]//div[contains(@class,'dropdown-content')]//p[contains(text(),'ONBL')]"
    ONBLOCK_SPAN = "//div[contains(@class,'arrival-time-col')]//div[contains(@class,'dropdown-content')]//p[contains(text(),'ONBL')]//span"

    # Departure time column & dropdown
    DEPARTURE_TIME_COL = "//div[contains(@class,'departure-time-col')]"
    DEPARTURE_DROPDOWN_CONTENT = "//div[contains(@class,'departure-time-col')]//div[contains(@class,'dropdown-content')]"
    OFFBLOCK_PARAGRAPH = "//div[contains(@class,'departure-time-col')]//div[contains(@class,'dropdown-content')]//p[contains(text(),'OFBL')]"
    OFFBLOCK_SPAN = "//div[contains(@class,'departure-time-col')]//div[contains(@class,'dropdown-content')]//p[contains(text(),'OFBL')]//span"

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

        # Move mouse away to dismiss navigation drawer
        self.page.mouse.move(700, 500)
        self.page.wait_for_timeout(1000)

        # Wait for any spinner to disappear
        try:
            self.page.locator(".loader-container, .spinner").wait_for(state="detached", timeout=15000)
        except Exception:
            pass

        logger.info("Successfully navigated to Flights List View dashboard")

    @allure.step("Switch to Section: '{section_name}' and Ensure Flights Loaded")
    def switch_to_section(self, section_name: str) -> int:
        """
        Switches to the specified section tab (Incoming, Ongoing, Departed).
        Waits for flight cards to load or triggers sync refresh if needed.
        Returns the total number of flight cards currently loaded.
        """
        tab_xpath = self.SECTIONS.get(section_name)
        if not tab_xpath:
            raise ValueError(f"Unknown section: '{section_name}'. Expected one of {list(self.SECTIONS.keys())}")

        logger.info(f"Switching to '{section_name}' section")
        tab_elem = self.page.locator(tab_xpath).first
        expect(tab_elem).to_be_visible(timeout=15000)
        tab_elem.click(force=True)
        self.page.wait_for_timeout(2000)

        card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
        try:
            card_loc.first.wait_for(state="visible", timeout=6000)
        except Exception:
            sync_icon = self.page.locator(self.SYNC_ICON).first
            if sync_icon.count() > 0 and sync_icon.is_visible():
                logger.info(f"Flight cards not immediately visible in {section_name}. Clicking Refresh Flight sync icon...")
                sync_icon.click()
                self.page.wait_for_timeout(3500)

        # Check for No Flights Available notification
        no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE).first
        if no_flights.count() > 0 and no_flights.is_visible():
            logger.info(f"Section '{section_name}' currently has 0 flights available.")
            return 0

        total_cards = card_loc.count()
        logger.info(f"Section '{section_name}' active with {total_cards} flight cards loaded")
        return total_cards

    @allure.step("Extract Flight Number for Card")
    def get_flight_number(self, flight_card: Locator) -> str:
        """Extracts arrival and departure flight number from the flight card."""
        num = super().get_flight_number(flight_card)
        if num and num != "Unknown Flight":
            return num
        num_loc = flight_card.locator(self.ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER).first
        if num_loc.count() > 0:
            return num_loc.inner_text().strip()
        return "Unknown Flight"

    @staticmethod
    def _is_valid_timestamp(val: str) -> bool:
        """
        Returns True if the string represents a valid timestamp (e.g. '10:45', '18/11/2026 10:45').
        Returns False for placeholders, dashes, '--:--', empty strings, etc.
        """
        if not val:
            return False
        clean = val.strip()
        if clean in ("--:--", "-", "N/A", "null", "None", ""):
            return False
        # Must contain at least two digits and a colon (time pattern HH:MM)
        return bool(re.search(r"\d{1,2}:\d{2}", clean))

    @allure.step("Parse Arrival Timings (STA, ETA, ONBL) for Flight Card")
    def parse_arrival_timings(self, flight_card: Locator) -> dict:
        """
        Hovers over the arrival time column to inspect the dropdown content.
        Extracts STA, ETA, and On-Block time (ONBL).
        Returns a dictionary with parsed timestamps and presence flags.
        """
        arr_col = flight_card.locator(self.ARRIVAL_TIME_COL).first
        if arr_col.count() > 0 and arr_col.is_visible():
            try:
                arr_col.hover()
                self.page.wait_for_timeout(300)
            except Exception:
                pass

        arr_dropdown = flight_card.locator(self.ARRIVAL_DROPDOWN_CONTENT).first
        raw_text = arr_dropdown.text_content() if arr_dropdown.count() > 0 else (arr_col.text_content() if arr_col.count() > 0 else "")
        raw_text = (raw_text or "").replace("\xa0", " ").strip()

        # Extract ONBL (On-block time)
        onbl_time = ""
        onbl_span = flight_card.locator(self.ONBLOCK_SPAN).first
        if onbl_span.count() > 0:
            candidate = onbl_span.inner_text().strip()
            if self._is_valid_timestamp(candidate):
                onbl_time = candidate

        if not onbl_time and "ONBL" in raw_text:
            m = re.search(r"ONBL\s*:\s*([0-9\/\-\s:]+)", raw_text)
            if m:
                candidate = m.group(1).strip()
                if self._is_valid_timestamp(candidate):
                    onbl_time = candidate

        # Extract STA
        sta_time = ""
        m_sta = re.search(r"STA\s*:\s*([0-9\/\-\s:]+)", raw_text)
        if m_sta and self._is_valid_timestamp(m_sta.group(1)):
            sta_time = m_sta.group(1).strip()

        # Extract ETA
        eta_time = ""
        m_eta = re.search(r"ETA\s*:\s*([0-9\/\-\s:]+)", raw_text)
        if m_eta and self._is_valid_timestamp(m_eta.group(1)):
            eta_time = m_eta.group(1).strip()

        # Dismiss hover
        self.page.mouse.move(0, 0)

        has_onblock = bool(onbl_time)
        return {
            "sta": sta_time,
            "eta": eta_time,
            "onblock_time": onbl_time,
            "has_onblock": has_onblock,
            "raw_text": raw_text.replace("\n", " | "),
        }

    @allure.step("Parse Departure Timings (STD, ETD, OFBL) for Flight Card")
    def parse_departure_timings(self, flight_card: Locator) -> dict:
        """
        Hovers over the departure time column to inspect the dropdown content.
        Extracts STD, ETD, and Off-Block time (OFBL).
        Returns a dictionary with parsed timestamps and presence flags.
        """
        dep_col = flight_card.locator(self.DEPARTURE_TIME_COL).first
        if dep_col.count() > 0 and dep_col.is_visible():
            try:
                dep_col.hover()
                self.page.wait_for_timeout(300)
            except Exception:
                pass

        dep_dropdown = flight_card.locator(self.DEPARTURE_DROPDOWN_CONTENT).first
        raw_text = dep_dropdown.text_content() if dep_dropdown.count() > 0 else (dep_col.text_content() if dep_col.count() > 0 else "")
        raw_text = (raw_text or "").replace("\xa0", " ").strip()

        # Extract OFBL (Off-block time)
        ofbl_time = ""
        ofbl_span = flight_card.locator(self.OFFBLOCK_SPAN).first
        if ofbl_span.count() > 0:
            candidate = ofbl_span.inner_text().strip()
            if self._is_valid_timestamp(candidate):
                ofbl_time = candidate

        if not ofbl_time and "OFBL" in raw_text:
            m = re.search(r"OFBL\s*:\s*([0-9\/\-\s:]+)", raw_text)
            if m:
                candidate = m.group(1).strip()
                if self._is_valid_timestamp(candidate):
                    ofbl_time = candidate

        # Extract STD
        std_time = ""
        m_std = re.search(r"STD\s*:\s*([0-9\/\-\s:]+)", raw_text)
        if m_std and self._is_valid_timestamp(m_std.group(1)):
            std_time = m_std.group(1).strip()

        # Extract ETD
        etd_time = ""
        m_etd = re.search(r"ETD\s*:\s*([0-9\/\-\s:]+)", raw_text)
        if m_etd and self._is_valid_timestamp(m_etd.group(1)):
            etd_time = m_etd.group(1).strip()

        # Dismiss hover
        self.page.mouse.move(0, 0)

        has_offblock = bool(ofbl_time)
        return {
            "std": std_time,
            "etd": etd_time,
            "offblock_time": ofbl_time,
            "has_offblock": has_offblock,
            "raw_text": raw_text.replace("\n", " | "),
        }

    @allure.step("Validate Flight Block-Times for Section: '{expected_section}'")
    def validate_flight_block_times(self, flight_card: Locator, expected_section: str) -> dict:
        """
        Validates whether the flight card satisfies the block-time rules for the target section:
          - 'Incoming': has_onblock == False AND has_offblock == False
          - 'Ongoing':  has_onblock == True  AND has_offblock == False
          - 'Departed': has_onblock == True  AND has_offblock == True
        """
        flight_card.scroll_into_view_if_needed()
        flight_no = self.get_flight_number(flight_card)
        arr = self.parse_arrival_timings(flight_card)
        dep = self.parse_departure_timings(flight_card)

        has_onblock = arr["has_onblock"]
        onblock_time = arr["onblock_time"]
        has_offblock = dep["has_offblock"]
        offblock_time = dep["offblock_time"]

        passed = False
        reason = ""

        if expected_section == "Incoming":
            # Rule: If flight is NOT having onblock and NOT having offblock -> must be in Incoming
            if not has_onblock and not has_offblock:
                passed = True
                reason = "Verified: Flight has NO On-block and NO Off-block time; correctly placed in Incoming section."
            else:
                passed = False
                reasons = []
                if has_onblock:
                    reasons.append(f"Has ONBL='{onblock_time}' (must transition to Ongoing)")
                if has_offblock:
                    reasons.append(f"Has OFBL='{offblock_time}' (must transition to Departed)")
                reason = f"Incoming Violation: {'; '.join(reasons)}"

        elif expected_section == "Ongoing":
            # Rule: If flight IS having onblock and DOES NOT have offblock -> must be in Ongoing
            if has_onblock and not has_offblock:
                passed = True
                reason = f"Verified: Flight has On-block (ONBL='{onblock_time}') and NO Off-block time; correctly placed in Ongoing section."
            else:
                passed = False
                if not has_onblock and not has_offblock:
                    reason = "Ongoing Violation: Flight lacks On-block time (belongs in Incoming section)."
                elif has_offblock:
                    reason = f"Ongoing Violation: Flight already has Off-block time (OFBL='{offblock_time}') (must transition to Departed section)."
                else:
                    reason = f"Ongoing Violation: ONBL_Present={has_onblock}, OFBL_Present={has_offblock}."

        elif expected_section == "Departed":
            # Rule: If flight IS having BOTH onblock and offblock -> must be in Departed
            if has_offblock:
                passed = True
                reason = f"Verified: Flight has Off-block (OFBL='{offblock_time}') and On-block (ONBL='{onblock_time}'); correctly placed in Departed section."
            else:
                passed = False
                reason = "Departed Violation: Flight lacks Off-block time (OFBL is absent)."

        if not passed:
            try:
                setattr(self.page, "_last_failed_locator", flight_card)
            except Exception:
                pass

        result = {
            "flight_number": flight_no,
            "section": expected_section,
            "has_onblock": has_onblock,
            "onblock_time": onblock_time,
            "has_offblock": has_offblock,
            "offblock_time": offblock_time,
            "passed": passed,
            "reason": reason,
            "arrival_details": arr,
            "departure_details": dep,
        }

        log_fn = logger.info if passed else logger.error
        log_fn(
            f"[{expected_section}] Flight '{flight_no}' => ONBL='{onblock_time}' (Has={has_onblock}), "
            f"OFBL='{offblock_time}' (Has={has_offblock}) | {'PASSED' if passed else 'FAILED'} | {reason}"
        )

        return result

    @allure.step("Validate Section Flights: '{section_name}'")
    def validate_section_flights(self, section_name: str, max_flights: int = 15) -> dict:
        """
        Switches to section_name, iterates over up to max_flights flight cards,
        and validates that each flight complies with the section's block-time rule.
        """
        total_cards = self.switch_to_section(section_name)
        if total_cards == 0:
            logger.info(f"Section '{section_name}' currently has 0 flights loaded; skipping inspection.")
            return {
                "section": section_name,
                "total_cards": 0,
                "inspected_count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "failed_cards": [],
                "results": [],
            }

        card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
        flights_to_inspect = min(card_loc.count(), max_flights)
        logger.info(f"Inspecting block times across {flights_to_inspect} flight cards in '{section_name}' section")

        results = []
        failed_cards = []

        for i in range(flights_to_inspect):
            card = card_loc.nth(i)
            res = self.validate_flight_block_times(card, expected_section=section_name)
            results.append(res)
            if not res["passed"]:
                failed_cards.append(res)

        passed_count = sum(1 for r in results if r["passed"])
        failed_count = len(failed_cards)

        return {
            "section": section_name,
            "total_cards": total_cards,
            "inspected_count": flights_to_inspect,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "failed_cards": failed_cards,
            "results": results,
        }

    @allure.step("Validate Flight Transitions & Block-Times Across Incoming, Ongoing, and Departed Sections")
    def validate_all_sections_flight_transitions(
        self,
        incoming_limit: int = 10,
        ongoing_limit: int = 15,
        departed_limit: int = 10,
    ) -> dict:
        """
        Executes end-to-end flight transition validation across all 3 key sections:
        1. Incoming: No On-block, No Off-block.
        2. Ongoing:  Has On-block, No Off-block.
        3. Departed: Has Both On-block and Off-block.
        Returns aggregated summary.
        """
        logger.info("Starting flight transition validation across Incoming, Ongoing, and Departed sections")

        ongoing_summary = self.validate_section_flights("Ongoing", max_flights=ongoing_limit)
        incoming_summary = self.validate_section_flights("Incoming", max_flights=incoming_limit)
        departed_summary = self.validate_section_flights("Departed", max_flights=departed_limit)

        total_inspected = (
            ongoing_summary["inspected_count"]
            + incoming_summary["inspected_count"]
            + departed_summary["inspected_count"]
        )
        total_failed = (
            ongoing_summary["failed_count"]
            + incoming_summary["failed_count"]
            + departed_summary["failed_count"]
        )

        all_failed_cards = (
            ongoing_summary["failed_cards"]
            + incoming_summary["failed_cards"]
            + departed_summary["failed_cards"]
        )

        return {
            "total_inspected": total_inspected,
            "total_failed": total_failed,
            "all_failed_cards": all_failed_cards,
            "ongoing": ongoing_summary,
            "incoming": incoming_summary,
            "departed": departed_summary,
        }
