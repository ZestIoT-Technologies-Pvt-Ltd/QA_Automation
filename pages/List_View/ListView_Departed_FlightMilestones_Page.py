# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

"""
==============  INTRODUCTION ================
Page Object: ListView_Departed_FlightMilestones_Page
Description: Page Object Model for the Departed section in Flights List View.
             Validates Flight Milestones popup functionality, milestone sequence,
             completion status bar, and actual timestamps.

Scenario & Workflow Capabilities:
1. Navigation: Route to Flights List View and select Departed section.
2. Action Menu: Click the ellipsis ('more_vert') menu on departed flight cards.
3. Open Milestones: Click 'Flight Milestones' option to display the milestones dialog popup.
4. Milestone Verification:
   - Verify milestones are present in the popup screen.
   - Verify strict sequence: 1) Ten Nautical Miles -> 2) Touchdown -> 3) Airborne (if airborne).
   - Verify milestone completion status bar / milestone items are displayed.
   - Verify actual timestamps are displayed for the milestones.
5. Cleanup: Close popup and click anywhere on the screen to dismiss any lingering
   menu tooltip before moving to the next flight card.
"""

from __future__ import annotations

import re
import allure
from typing import Any, Dict, List, Optional
from playwright.sync_api import expect, Locator

from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Departed_FlightMilestones_Page(BasePage):
    """
    Page Object for Flights List View Departed Section - Flight Milestones validation.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    LIST_VIEW = "//div[@role='button']//span[normalize-space()='Flights'] | //span[normalize-space()='Flights']"

    DEPARTED_TAB = "text=Departed"
    SECTIONS = {
        "Departed": "text=Departed",
        "Ongoing": "text=Ongoing",
        "Incoming": "text=Incoming",
    }

    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
    FLIGHT_NUMBER = (
        "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
        "//div[contains(@class,'flightno-col')] | "
        "//p[@mattooltip='Flight Arrival Departure Numbers']"
    )
    SYNC_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # Ellipsis action menu on flight card
    ELLIPSIS_MENU_ICON = "mat-icon:has-text('more_vert')"
    THREE_DOTS_MENU_ICON = ELLIPSIS_MENU_ICON  # Backwards compatibility

    # Flight Milestones Dialog / Popup (PrimeNG p-dialog or dialog container with Milestone header)
    MILESTONES_DIALOG = (
        "//div[contains(@class,'p-dialog') and not(contains(@class,'hidden'))] | "
        "//div[@role='dialog'][.//*[contains(text(),'Milestone')]] | "
        "//mat-dialog-container[.//h1[contains(text(),'Milestone')] or .//*[contains(text(),'Flight Milestones')]]"
    )

    @allure.step("Navigate to Flights List View Dashboard")
    def navigate_to_list_view_page(self):
        """
        Navigates from the home dashboard to the Flights List View screen.

        What this function does:
        Opens the main navigation menu on the top-left and clicks on the 'Flights' option
        so that the user is brought directly to the Flights List View dashboard.

        Step-by-step actions:
        1. Hovers over the top-left navigation menu icon.
        2. Clicks on the 'Flights' menu option.
        3. Moves the mouse away towards the center of the screen so the menu drawer closes.
        4. Waits for any loading spinners to complete.
        """
        logger.info("Navigating to Flights List View dashboard")
        self.page.wait_for_timeout(2000)

        # Locate and hover over the navigation menu icon
        menu = self.page.locator(self.MENU).first
        expect(menu).to_be_visible(timeout=20000)
        menu.hover()
        self.page.wait_for_timeout(500)

        # Locate and click on the 'Flights' option
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
            self.page.locator(".loader-container, .spinner, .mat-progress-spinner").wait_for(state="detached", timeout=15000)
        except Exception:
            pass

        logger.info("Successfully navigated to Flights List View dashboard")

    #@allure.step("Select Departed Section and Ensure Flights Loaded")
    def ensure_departed_section_loaded(self) -> int:
        """
        Switches to the 'Departed' flights section and verifies flight cards are loaded.

        What this function does:
        Clicks on the 'Departed' tab at the top of the Flights List View screen to display
        all flights that have departed. It counts how many departed flight cards are visible.

        Step-by-step actions:
        1. Finds and clicks the 'Departed' tab button.
        2. Waits for any loading spinners to finish.
        3. If flight cards do not appear immediately, clicks the Refresh Flight icon to reload them.
        4. Checks if there is a 'No Flights Available' message. If so, returns 0.
        5. Returns the total count of departed flight cards displayed on the screen.

        Returns:
            int: The total count of departed flight cards currently loaded.
        """
        logger.info("Selecting Departed section tab")
        self.page.wait_for_timeout(1000)

        # Locate and click the 'Departed' tab button
        departed_tab = self.page.locator(self.DEPARTED_TAB).first
        if departed_tab.count() == 0 or not departed_tab.is_visible():
            departed_tab = self.page.locator(
                "//div[contains(.,'Departed') and not(contains(@class,'card'))] | "
                "//span[contains(text(),'Departed')]"
            ).first

        expect(departed_tab).to_be_visible(timeout=15000)
        departed_tab.scroll_into_view_if_needed()
        departed_tab.click()
        self.page.wait_for_timeout(2500)

        # Wait for loading spinners to finish
        try:
            self.page.locator(".loader-container, .spinner, .mat-progress-spinner, .loading").wait_for(state="detached", timeout=15000)
        except Exception:
            pass

        # Check if flight cards are visible; if not, try clicking the refresh icon
        card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
        try:
            card_loc.first.wait_for(state="visible", timeout=8000)
        except Exception:
            sync_icon = self.page.locator(self.SYNC_ICON).first
            if sync_icon.count() > 0 and sync_icon.is_visible():
                logger.info("Departed flight cards not immediately visible. Triggering Refresh Flight sync icon...")
                sync_icon.click()
                self.page.wait_for_timeout(3500)

        # Check if no flights are available in this section
        no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE).first
        if no_flights.count() > 0 and no_flights.is_visible():
            logger.info("Departed section currently has 0 flights available.")
            return 0

        total_cards = card_loc.count()
        logger.info(f"Departed section active with {total_cards} flight cards loaded")
        return total_cards

    #@allure.step("Extract Flight Number for Card")
    def get_flight_number(self, flight_card: Locator) -> str:
        """
        Reads and returns the flight number from a flight card.

        What this function does:
        Inspects the flight card element and extracts the flight number text
        (for example, 'FZ-0215').

        Inputs:
            flight_card (Locator): The flight card web element to read from.

        Returns:
            str: The flight number text, or 'Unknown Flight' if not found.
        """
        num = super().get_flight_number(flight_card)
        if num and num != "Unknown Flight":
            return num
        num_loc = flight_card.locator(self.FLIGHT_NUMBER).first
        if num_loc.count() > 0:
            return num_loc.inner_text().strip()
        return "Unknown Flight"

    @allure.step("Open Flight Milestones Popup from Ellipsis Menu")
    def open_flight_milestones_popup(self, flight_card: Locator) -> bool:
        """
        Opens the Flight Milestones popup window for a flight card.

        What this function does:
        Clicks the three-dot ellipsis menu button on the flight card, then clicks the
        'Flight Milestones' option to open the milestone details popup dialog.

        Step-by-step actions:
        1. Scrolls the flight card into view.
        2. Clicks the ellipsis (more_vert) menu button on the card.
        3. Clicks the 'Flight Milestones' item in the menu dropdown.
        4. Verifies that the Flight Milestones dialog window appears on the screen.

        Inputs:
            flight_card (Locator): The flight card whose milestones we want to view.

        Returns:
            bool: True if the popup opened successfully.
        """
        flight_card.scroll_into_view_if_needed()
        flight_no = self.get_flight_number(flight_card)
        logger.info(f"Opening ellipsis menu for flight '{flight_no}'")

        # 1. Locate and click ellipsis menu icon strictly on the target flight card
        ellipsis_menu = flight_card.locator(self.ELLIPSIS_MENU_ICON).first
        expect(ellipsis_menu).to_be_visible(timeout=10000)
        ellipsis_menu.scroll_into_view_if_needed()
        ellipsis_menu.click()
        self.page.wait_for_timeout(400)

        # 2. Locate and click 'Flight Milestones' option in the menu dropdown
        milestone_option = self.page.get_by_role("menuitem", name=re.compile(r"Flight Milestones", re.IGNORECASE)).first
        if milestone_option.count() == 0 or not milestone_option.is_visible():
            milestone_option = self.page.locator(
                "//button[contains(@class,'mat-menu-item') and contains(.,'Flight Milestones')] | "
                "//button[contains(.,'Flight Milestones')] | "
                "//span[normalize-space()='Flight Milestones']"
            ).first

        expect(milestone_option).to_be_visible(timeout=10000)
        logger.info(f"Clicking 'Flight Milestones' option in ellipsis menu for flight '{flight_no}'")
        milestone_option.click()
        self.page.wait_for_timeout(1000)

        # 3. Verify Milestones popup appears on the screen
        dialog = self.page.locator(self.MILESTONES_DIALOG).first
        try:
            expect(dialog).to_be_visible(timeout=15000)
            logger.info(f"Flight Milestones popup displayed successfully for flight '{flight_no}'")
            return True
        except Exception:
            setattr(self.page, "_last_failed_locator", ellipsis_menu)
            raise AssertionError(f"Flight Milestones popup did not appear after clicking menu item for flight '{flight_no}'")

    @allure.step("Close Flight Milestones Popup")
    def close_flight_milestones_popup(self) -> bool:
        """
        Closes the Flight Milestones dialog popup.

        What this function does:
        Finds and clicks the 'X' (close) button at the top corner of the milestone popup
        dialog, or presses the Escape key on the keyboard to dismiss the popup window.

        Returns:
            bool: True once the popup is closed.
        """
        logger.info("Closing Flight Milestones dialog popup")
        dialog = self.page.locator(self.MILESTONES_DIALOG).first

        if dialog.count() == 0 or not dialog.is_visible():
            logger.info("Flight Milestones dialog is not visible or already closed")
            return True

        closed = False

        # Attempt clicking close button inside dialog header
        close_btn = dialog.locator(
            "button.p-dialog-header-close, "
            "span.p-dialog-header-close-icon, "
            ".p-dialog-header-close, "
            "button[aria-label='Close'], "
            "button:has-text('✕'), "
            "button:has-text('×'), "
            "mat-icon:has-text('close')"
        ).first

        if close_btn.count() > 0 and close_btn.is_visible():
            logger.info("Clicking popup header close button")
            close_btn.click()
            self.page.wait_for_timeout(400)
            if not dialog.is_visible():
                closed = True

        # Fallback: Press Escape on the keyboard
        if not closed and dialog.is_visible():
            logger.info("Pressing Escape to dismiss Flight Milestones popup")
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(400)
            if not dialog.is_visible():
                closed = True

        # Confirm dialog is hidden
        try:
            expect(dialog).to_be_hidden(timeout=5000)
            logger.info("Flight Milestones dialog successfully closed")
        except Exception:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)

        return True

    @allure.step("Click Anywhere on Screen to Dismiss Tooltips")
    def dismiss_lingering_tooltip(self):
        """
        Clicks anywhere on a neutral area of the screen to dismiss leftover tooltips.

        What this function does:
        Clicks on an empty space on the screen so that any remaining tooltip, hover box,
        or menu overlay disappears before we move on to inspect the next flight.
        """
        try:
            # Click at neutral coordinates on the screen
            self.page.mouse.click(200, 200)
            self.page.wait_for_timeout(400)
        except Exception as e:
            logger.warning(f"Could not click neutral area on screen: {e}")

    @allure.step("Check and Validate Flight Milestones Sequence & Timestamps in Popup")
    def parse_and_validate_milestones_popup(self) -> dict:
        """
        Inspects the open Flight Milestones popup window and verifies its content.

        What this function does:
        Reads all text and elements inside the milestones popup to confirm:
        1. That flight milestones are present on the screen.
        2. That they appear in the correct chronological order:
           - First: 'Ten Nautical Miles' (flight is approaching)
           - Second: 'Touchdown' (flight has landed)
           - Third: 'Airborne' (flight has taken off again, if applicable)
        3. That the milestone completion status bar / milestone items are visible.
        4. That actual times (timestamps like '14:30') are recorded and displayed.

        Returns:
            dict: A detailed results dictionary containing sequence verification,
                  completion status bar check, timestamps found, and raw text.
        """
        dialog = self.page.locator(self.MILESTONES_DIALOG).first
        expect(dialog).to_be_visible(timeout=10000)

        # Wait briefly for milestone content to load inside popup
        self.page.wait_for_timeout(800)
        try:
            dialog.locator("text=/Ten Nautical Miles|Touchdown|Airborne/i").first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

        raw_text = dialog.inner_text().strip()
        logger.info(f"Milestones Popup Text Content:\n{raw_text}")

        norm_text = raw_text.lower()

        # 1. Milestone Presence & Sequence Check:
        # Expected sequence: 1) Ten Nautical Miles -> 2) Touchdown -> 3) Airborne (if airborne)
        has_ten_nm = bool(
            re.search(r"ten\s+nautical\s+mile|10\s*nm|10\s+nautical\s+mile", norm_text)
        )
        has_touchdown = bool(
            re.search(r"touchdown|touch\s+down|tdn", norm_text)
        )
        has_airborne = bool(
            re.search(r"airborne|air\s*born|abn", norm_text)
        )

        pos_ten_nm = -1
        m1 = re.search(r"ten\s+nautical\s+mile|10\s*nm|10\s+nautical\s+mile", norm_text)
        if m1:
            pos_ten_nm = m1.start()

        pos_touchdown = -1
        m2 = re.search(r"touchdown|touch\s+down|tdn", norm_text)
        if m2:
            pos_touchdown = m2.start()

        pos_airborne = -1
        m3 = re.search(r"airborne|air\s*born|abn", norm_text)
        if m3:
            pos_airborne = m3.start()

        sequence_correct = False
        if has_ten_nm and has_touchdown:
            if has_airborne:
                sequence_correct = (pos_ten_nm < pos_touchdown < pos_airborne)
            else:
                sequence_correct = (pos_ten_nm < pos_touchdown)

        # 2. Completion Status Bar / Milestones Displayed:
        status_bar_displayed = has_ten_nm and has_touchdown

        # 3. Actual Timestamps Check:
        timestamps_found = re.findall(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", raw_text)
        has_actual_timestamps = len(timestamps_found) > 0

        # Detailed check for Airborne completion / timestamp:
        airborne_completed = False
        airborne_timestamp = ""
        if has_airborne and pos_airborne != -1:
            airborne_section = raw_text[pos_airborne : pos_airborne + 150]
            m_time = re.search(r"\b\d{1,2}:\d{2}\b", airborne_section)
            if m_time:
                airborne_timestamp = m_time.group(0)
                airborne_completed = True
            elif any(k in airborne_section.lower() for k in ("done", "completed", "actual", "tick", "success")):
                airborne_completed = True

        ten_nm_timestamp = ""
        if has_ten_nm and pos_ten_nm != -1:
            ten_nm_sec = raw_text[pos_ten_nm : pos_ten_nm + 150]
            m_t = re.search(r"\b\d{1,2}:\d{2}\b", ten_nm_sec)
            if m_t:
                ten_nm_timestamp = m_t.group(0)

        touchdown_timestamp = ""
        if has_touchdown and pos_touchdown != -1:
            tdn_sec = raw_text[pos_touchdown : pos_touchdown + 150]
            m_t = re.search(r"\b\d{1,2}:\d{2}\b", tdn_sec)
            if m_t:
                touchdown_timestamp = m_t.group(0)

        result = {
            "has_ten_nm": has_ten_nm,
            "has_touchdown": has_touchdown,
            "has_airborne": has_airborne,
            "pos_ten_nm": pos_ten_nm,
            "pos_touchdown": pos_touchdown,
            "pos_airborne": pos_airborne,
            "sequence_correct": sequence_correct,
            "status_bar_displayed": status_bar_displayed,
            "has_actual_timestamps": has_actual_timestamps,
            "timestamps_found": timestamps_found,
            "ten_nm_timestamp": ten_nm_timestamp,
            "touchdown_timestamp": touchdown_timestamp,
            "airborne_completed": airborne_completed,
            "airborne_timestamp": airborne_timestamp,
            "raw_text": raw_text.replace("\n", " | "),
        }

        logger.info(
            f"Milestone Parsing Result -> SequenceCorrect={sequence_correct}, "
            f"StatusBarDisplayed={status_bar_displayed}, HasTimestamps={has_actual_timestamps} "
            f"(Found={timestamps_found}), AirborneCompleted={airborne_completed} (Time='{airborne_timestamp}')"
        )

        return result

    @allure.step("Validate Flight Milestones for Flight Card")
    def validate_flight_milestones_card(self, flight_card: Locator) -> dict:
        """
        Executes end-to-end validation for a departed flight card:
        1. Opens Flight Milestones popup from ellipsis menu.
        2. Validates milestone presence & sequence (Ten Nautical Miles -> Touchdown -> Airborne).
        3. Validates completion status bar / milestones displayed.
        4. Validates actual timestamps are displayed.
        5. Closes popup.
        6. Clicks anywhere on the screen to dismiss any lingering menu tooltip.
        """
        flight_card.scroll_into_view_if_needed()
        flight_no = self.get_flight_number(flight_card)
        logger.info(f"--- Validating Milestones for Flight: '{flight_no}' ---")

        # Step 1: Open popup from ellipsis menu
        self.open_flight_milestones_popup(flight_card)

        # Step 2: Parse milestones popup
        milestones_data = self.parse_and_validate_milestones_popup()

        # Step 3: Close popup
        #self.close_flight_milestones_popup()

        # Step 4: Click anywhere on screen to dismiss any lingering menu tooltip
        #logger.info("Clicking anywhere on screen to dismiss menu tooltip")
        #self.dismiss_lingering_tooltip()

        # Assertions logic
        passed = True
        reasons = []

        if not (milestones_data["has_ten_nm"] and milestones_data["has_touchdown"]):
            passed = False
            reasons.append("Milestones 'Ten Nautical Miles' or 'Touchdown' missing from popup")

        if not milestones_data["sequence_correct"]:
            passed = False
            reasons.append("Milestone sequence is incorrect (Expected: Ten Nautical Miles -> Touchdown -> Airborne)")

        if not milestones_data["status_bar_displayed"]:
            passed = False
            reasons.append("Completion status bar / milestone items not displayed in popup")

        if not milestones_data["has_actual_timestamps"]:
            passed = False
            reasons.append("Actual timestamps not displayed for milestones in popup")

        result = {
            "flight_number": flight_no,
            "passed": passed,
            "reasons": reasons,
            "milestones_data": milestones_data,
        }

        log_fn = logger.info if passed else logger.error
        log_fn(
            f"Flight '{flight_no}' Validation => Passed={passed} | "
            f"SequenceCorrect={milestones_data['sequence_correct']}, "
            f"StatusBar={milestones_data['status_bar_displayed']}, "
            f"Timestamps={milestones_data['has_actual_timestamps']}"
        )

        return result
