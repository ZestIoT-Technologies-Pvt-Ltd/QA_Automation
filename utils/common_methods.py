# Author : Tilak Badsheshi
# Created Date : 2026-11-20
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-20

"""
==============  INTRODUCTION ================
Module: utils.common_methods
Description: Centralized Common Methods Library for the AviLeap QA Automation framework.
             Contains universal, application-level actions that are performed repeatedly across
             the application — such as refreshing the page or flights list, clicking neutral screen
             areas to dismiss popups and tooltips, waiting for loading spinners, capturing screenshots,
             and extracting flight numbers from class="flightno-col".

What is included in this file:
1. Refresh Actions:
   - Refresh the entire web page.
   - Refresh the flights list by clicking the circular sync icon on the toolbar.
2. Screen Click & Dismiss Actions:
   - Click outside / neutral screen coordinate to close open menus or overlays.
   - Dismiss lingering tooltips that may block other elements.
   - Move mouse away to neutral coordinates so hover drawers collapse cleanly.
3. Loading & Spinner Synchronization:
   - Wait for application loading spinners (.loading, .spinner, .mat-progress-spinner) to disappear.
   - Wait for DOM and network idle states.
4. Evidence & Screenshot Attachment:
   - Capture PNG screenshots and attach directly to Allure reports and logs.
5. Universal Flight Number Extraction:
   - Extract Arrival and Departure flight numbers from class="flightno-col".
   - Return clean formatted flight number strings for report steps and logs.
"""

from __future__ import annotations

import re
import time
from typing import Any
import allure
from playwright.sync_api import Locator, Page, expect
from utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Universal Application Locators
# =============================================================================

REFRESH_FLIGHTS_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"
SPINNER_SELECTORS = [
    ".loading",
    ".spinner",
    ".mat-progress-spinner",
    ".loader-container",
    "p-progress-spinner",
]
FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = (
    "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
    "//div[contains(@class,'flightno-col')] | "
    "//p[@mattooltip='Flight Arrival Departure Numbers']"
)
FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]"


# =============================================================================
# Standalone Helper Functions
# =============================================================================

def is_valid_timestamp(val: str) -> bool:
    """
    Checks if a given string represents a valid timestamp (e.g., '10:45', '18/11/2026 10:45').

    What this function does:
    Checks if the input text contains digits and a colon matching a time format.
    Returns False for placeholder dashes ('--', '-'), 'N/A', 'null', or empty values.

    Inputs:
        val (str): The text string to evaluate.

    Returns:
        bool: True if the string looks like a real time, False otherwise.
    """
    if not val:
        return False
    clean = str(val).strip()
    if clean in ("--:--", "-", "--", "N/A", "null", "None", ""):
        return False
    return bool(re.search(r"\d{1,2}:\d{2}", clean))


def parse_flight_numbers_from_text(raw_text: str) -> tuple[str, str]:
    """
    Parses a raw flight string into separate arrival and departure flight numbers.

    What this function does:
    Takes a raw string like '8500 - 863' or 'FZ-0215 - FZ-0216' and splits it by common
    delimiters (' - ', ' / ', '-') to return the individual arrival and departure flight numbers.

    Inputs:
        raw_text (str): Raw text containing flight numbers.

    Returns:
        tuple[str, str]: (arrival_flight_number, departure_flight_number).
    """
    if not raw_text:
        return "", ""
    clean = " ".join(raw_text.split())
    if " - " in clean:
        parts = clean.split(" - ", 1)
        arr = parts[0].strip()
        dep = parts[1].strip() if len(parts) > 1 else ""
        return (arr if arr != "-" else ""), (dep if dep != "-" else "")
    if " / " in clean:
        parts = clean.split(" / ", 1)
        arr = parts[0].strip()
        dep = parts[1].strip() if len(parts) > 0 else ""
        return (arr if arr != "-" else ""), (dep if dep != "-" else "")
    if "-" in clean and not clean.startswith("FZ-") and not clean.startswith("EK-"):
        parts = clean.split("-", 1)
        arr = parts[0].strip()
        dep = parts[1].strip() if len(parts) > 1 else ""
        return (arr if arr != "-" else ""), (dep if dep != "-" else "")
    return clean, ""


def login_to_application(page: Page, username: str | None = None, password: str | None = None):
    """
    Universal prerequisite action to log into the AviLeap application.

    What this function does:
    Signs into the application using configured user credentials so that
    protected flight dashboards can be accessed by any test script.
    It removes the need to write login boilerplate in every single test file.

    Inputs:
        page (Page): The active Playwright browser page.
        username (str, optional): Account username (uses config if None).
        password (str, optional): Account password (uses config if None).

    Returns:
        LoginPage: The authenticated login page instance.
    """
    from pages.Login.Login_Page import LoginPage
    login_page = LoginPage(page)
    login_page.login_user(username=username, password=password)
    return login_page


# =============================================================================
# CommonMethods Library Class
# =============================================================================

class CommonMethods:
    """
    Common Methods Library class providing universal application-level actions.
    These methods handle general application tasks like refreshing, clicking outside,
    waiting for spinners, capturing screenshots, and parsing flight numbers.
    """

    REFRESH_FLIGHTS_ICON = REFRESH_FLIGHTS_ICON
    SPINNER_SELECTORS = SPINNER_SELECTORS
    FLIGHTNO_COL = FLIGHTNO_COL
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER
    FLIGHT_ROW_CARDS = FLIGHT_ROW_CARDS

    def __init__(self, page: Page | None = None):
        """
        Initializes the CommonMethods library.

        Inputs:
            page (Page, optional): The active Playwright Page instance.
        """
        self.page = page

    def login(self, username: str | None = None, password: str | None = None):
        """
        Signs the test user into the AviLeap application as a prerequisite.

        Inputs:
            username (str, optional): Account username.
            password (str, optional): Account password.
        """
        if not self.page:
            raise ValueError("Browser page instance is required to log in.")
        return login_to_application(self.page, username=username, password=password)

    def get_flight_cards(self, page: Page | None = None) -> Locator:
        """
        Finds all flight row cards currently rendered on the screen.

        What this function does:
        Locates all flight cards matching class="listviewmatcard" across
        Ongoing, Incoming, or Departed flight sections.

        Inputs:
            page (Page, optional): Browser page (defaults to self.page).

        Returns:
            Locator: Playwright Locator for the list of flight cards.
        """
        target = page or self.page
        if not target:
            raise ValueError("Browser page instance is required.")
        return target.locator(self.FLIGHT_ROW_CARDS)

    def get_first_flight_card(self, page: Page | None = None) -> Locator:
        """
        Finds the very first flight card currently visible on the screen.

        What this function does:
        Returns the first flight card on the active screen so tests can
        quickly target a flight without re-typing locator queries.

        Inputs:
            page (Page, optional): Browser page (defaults to self.page).

        Returns:
            Locator: Playwright Locator for the first flight card.
        """
        return self.get_flight_cards(page).first

    # =========================================================================
    # 1. Refresh Actions
    # =========================================================================

    def refresh_page(self, page: Page | None = None):
        """
        Reloads the current browser page and waits for DOM and network to settle.

        What this function does:
        Refreshes the current URL in the browser window, then pauses to ensure
        all network requests finish loading before proceeding.

        Inputs:
            page (Page, optional): The browser page to refresh (defaults to self.page).
        """
        target = page or self.page
        if target:
            logger.info("Refreshing current browser page...")
            target.reload(wait_until="domcontentloaded")
            self.wait_for_loading_to_finish(target)
            logger.info("Browser page reloaded successfully")

    def refresh_flights_list(self, page: Page | None = None, timeout: int = 20000):
        """
        Clicks the circular Refresh Flight sync icon on the toolbar to reload flights data.

        What this function does:
        1. Moves the mouse away from the toolbar so it isn't obstructed by tooltips.
        2. Locates and clicks the circular sync/refresh button on the toolbar.
        3. Waits for any loading animation or spinner to finish.
        4. Verifies that the flight cards reappear updated on the screen.

        Inputs:
            page (Page, optional): The active browser page (defaults to self.page).
            timeout (int): Maximum time in milliseconds to wait for the reload (default: 20 seconds).
        """
        target = page or self.page
        if not target:
            return
        logger.info("Clicking Refresh Flight sync icon on toolbar...")
        try:
            # Move mouse away to clear hover overlays
            target.mouse.move(600, 500)
            target.wait_for_timeout(500)

            refresh_icon = target.locator(self.REFRESH_FLIGHTS_ICON).first
            expect(refresh_icon).to_be_visible(timeout=10000)
            refresh_icon.click()
            logger.info("Clicked Refresh Flight icon")

            # Wait for spinner to appear and finish
            target.wait_for_timeout(1000)
            self.wait_for_loading_to_finish(target, timeout=timeout)

            # Wait for flight cards to be stable
            flights = target.locator(self.FLIGHT_ROW_CARDS)
            flights.first.wait_for(state="visible", timeout=timeout)
            target.wait_for_timeout(1500)
            logger.info("Flights list refreshed successfully. Total cards: %d", flights.count())

        except Exception as e:
            self.attach_screenshot("refresh_flights_failed", page=target)
            logger.error("Failed to refresh flights list: %s", e)
            raise

    # =========================================================================
    # 2. Screen Click & Dismiss Actions (Click Somewhere on Screen)
    # =========================================================================

    def click_outside(self, page: Page | None = None, x: int = 50, y: int = 50):
        """
        Clicks in a neutral, safe area of the screen to close any open dropdowns or menus.

        What this function does:
        Performs a mouse click at a specified coordinate (e.g., top-left corner x=50, y=50)
        away from any interactive buttons. This automatically causes floating menus,
        dropdowns, or focus rings to collapse cleanly.

        Inputs:
            page (Page, optional): The browser page (defaults to self.page).
            x (int): Horizontal pixel position to click (default: 50).
            y (int): Vertical pixel position to click (default: 50).
        """
        target = page or self.page
        if target:
            try:
                target.mouse.click(x, y)
                target.wait_for_timeout(300)
                logger.info("Clicked neutral screen coordinate (%d, %d) to dismiss overlays", x, y)
            except Exception:
                pass

    def dismiss_tooltip(self, page: Page | None = None):
        """
        Safely dismisses any hovering tooltip that might block other screen elements.

        What this function does:
        Moves the mouse cursor to a safe corner and performs a light click on the page body
        so that any hovering text tooltip disappears before the next action is clicked.

        Inputs:
            page (Page, optional): The browser page (defaults to self.page).
        """
        target = page or self.page
        if target:
            try:
                target.mouse.move(10, 10)
                target.locator("body").click(position={"x": 20, "y": 20}, force=True)
                target.wait_for_timeout(300)
            except Exception:
                pass

    def move_mouse_away(self, page: Page | None = None, x: int = 600, y: int = 500):
        """
        Moves the mouse cursor away to the center of the screen to collapse hover menus.

        What this function does:
        When hovering over a navigation drawer or toolbar button, moving the mouse to a neutral
        spot allows the opened menu or drawer to close naturally without clicking anything.

        Inputs:
            page (Page, optional): The browser page (defaults to self.page).
            x (int): Horizontal coordinate (default: 600).
            y (int): Vertical coordinate (default: 500).
        """
        target = page or self.page
        if target:
            try:
                target.mouse.move(x, y)
                target.wait_for_timeout(300)
            except Exception:
                pass

    # =========================================================================
    # 3. Loading Spinners & Synchronization
    # =========================================================================

    def wait_for_loading_to_finish(self, page: Page | None = None, timeout: int = 15000):
        """
        Waits for all loading spinners and progress animations on the page to disappear.

        What this function does:
        Checks if any loading animations (.loading, .spinner, .mat-progress-spinner,
        .loader-container, p-progress-spinner) are currently active on the screen.
        If they are, it waits until they finish so actions do not fail on an incomplete page.

        Inputs:
            page (Page, optional): The browser page (defaults to self.page).
            timeout (int): Maximum time in milliseconds to wait for spinners to hide (default: 15 seconds).
        """
        target = page or self.page
        if not target:
            return
        try:
            for selector in self.SPINNER_SELECTORS:
                spinners = target.locator(selector)
                count = spinners.count()
                for index in range(count):
                    spinner = spinners.nth(index)
                    if spinner.is_visible():
                        expect(spinner).not_to_be_visible(timeout=timeout)
            logger.info("Loading completed successfully")
        except Exception:
            pass

    # =========================================================================
    # 4. Evidence & Screenshots
    # =========================================================================

    def attach_screenshot(self, name: str, full_page: bool = True, page: Page | None = None):
        """
        Captures a picture of the current browser screen and attaches it to the test report.

        What this function does:
        Takes a screenshot of the browser window and attaches it to the Allure report and logs.
        Helps non-technical readers verify each step visually and troubleshoot any test failures.

        Inputs:
            name (str): A descriptive name for the image (e.g., 'flight_card_opened').
            full_page (bool): Set to True to capture the entire scrollable page (default: True).
            page (Page, optional): The browser page (defaults to self.page).
        """
        target = page or self.page
        if not target:
            return
        try:
            screenshot = target.screenshot(full_page=full_page)
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
            logger.info("Screenshot attached: %s", name)
        except Exception as e:
            logger.warning("Failed to attach screenshot %s: %s", name, e)

    # =========================================================================
    # 5. Flight Number Extraction (class="flightno-col")
    # =========================================================================

    def get_arrival_and_departure_flight_numbers(
        self,
        flight_card: Locator | None = None,
        page: Page | None = None
    ) -> tuple[str, str]:
        """
        Extracts both the Arrival Flight Number and Departure Flight Number from class="flightno-col".

        What this function does:
        1. Finds the flight number container element (class="flightno-col") on the flight card.
        2. Extracts text from child paragraph/tooltip elements.
        3. Parses and returns a clean tuple: (arrival_flight_number, departure_flight_number).

        Inputs:
            flight_card (Locator, optional): The flight card web element.
            page (Page, optional): The page instance (used if flight_card is None).

        Returns:
            tuple[str, str]: (arrival_flight_number, departure_flight_number).
        """
        target = flight_card if flight_card is not None else (page or self.page)
        if target is None:
            return "", ""
        try:
            col = target.locator(self.FLIGHTNO_COL).first
            raw_text = ""
            if col.count() > 0:
                p_elem = col.locator("p[mattooltip='Flight Arrival Departure Numbers'], p").first
                if p_elem.count() > 0:
                    raw_text = p_elem.inner_text().strip()
                if not raw_text:
                    raw_text = col.inner_text().strip()

            if not raw_text:
                tooltip_elem = target.locator("//p[@mattooltip='Flight Arrival Departure Numbers']").first
                if tooltip_elem.count() > 0:
                    raw_text = tooltip_elem.inner_text().strip()

            if raw_text:
                return parse_flight_numbers_from_text(raw_text)
        except Exception as e:
            logger.warning("Error fetching arrival and departure flight numbers: %s", e)
        return "", ""

    def get_flight_number(
        self,
        flight_card: Locator | None = None,
        page: Page | None = None
    ) -> str:
        """
        Extracts and formats a clean flight number string from class="flightno-col".

        What this function does:
        Extracts arrival and departure numbers and returns a clean human-readable flight string:
        - Turnaround: '8500 - 863' or 'FZ-0215 - FZ-0216'
        - Arrival only: 'FZ-0215'
        - Departure only: 'FZ-0216'

        Inputs:
            flight_card (Locator, optional): The flight card element.
            page (Page, optional): The page instance (used if flight_card is None).

        Returns:
            str: The formatted flight number string.
        """
        arr, dep = self.get_arrival_and_departure_flight_numbers(flight_card, page=page)
        if arr and dep:
            return f"{arr} - {dep}"
        if arr:
            return arr
        if dep:
            return dep
        return ""

