# Author : Gowthami Ankem
# Created Date : 2026-11-18
# Author : Gowthami Ankem
# Modified Date : 2026-11-23

"""
==============  INTRODUCTION ================
Page Object: ListView_Departed_DelayCode_Page
Description: Delay Codes validation in Flights List View.
             Handles inspection of delay code icons on departed flight cards, verification of green
             status, opening the Delay Codes popup, and validating that the summary metrics
             ('Codes Entered' and 'Total Delay Mins') accurately match the delay codes table rows
             and entered minutes below.

Workflow Capabilities:
1. Navigate to Flights List View and switch to the Departed section tab.
2. Inspect each Departed flight card for a Delay Code icon.
3. Check if the Delay Code icon is green 
4. If the icon is NOT green, leave/skip the flight.
5. If the icon is green, click to open the Delay Codes Popup.
6. Extract summary values: 'Codes Entered' and 'Total Delay Mins'.
7. Validate that the table below contains matching number of delay code rows and total delay minutes.
8. Safely close the Popup and continue with subsequent flights.
"""

import re
import time
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Departed_DelayCode_Page(BasePage):
    
    # ==================== NAVIGATION LOCATORS ====================
    MENU = (
        "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu'] | "
        "//mat-icon[normalize-space()='menu' or text()='menu'] | "
        "//span[contains(@class,'nav-icon')] | "
        "//button[contains(@aria-label, 'menu')]"
    )
    FLIGHTS = (
        "//div[@role='button' and contains(@class,'nav-row')][.//span[normalize-space()='Flights']] | "
        "//span[normalize-space()='Flights'] | "
        "//div[contains(@class,'nav-row')]//span[contains(text(),'Flights')]"
    )
    DEPARTED_TAB = "text=Departed"
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    FLIGHT_NUMBER = "//p[@mattooltip='Flight Arrival Departure Numbers']"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # ==================== DELAY CODE ICON LOCATOR ====================
    DELAY_CODE_ICON = (
        "mat-icon[mattooltip*='Delay'], "
        "mat-icon[mattooltip*='delay'], "
        "mat-icon.addeddelaycode, "
        "mat-icon:has-text('add_circle_outline')"
    )

    # ==================== DELAY CODES POPUP LOCATORS ====================
    DELAY_POPUP = (
        ".DelaycodesClass, "
        ".DelaycodesClassdark, "
        "app-delaycodes, "
        "div[role='dialog']:has(app-delaycodes)"
    )
    HEADER_FLIGHT_NAMES = ".header_flights_name"
    HEADER_DELAY_MINS = ".delay_mins"

    CODES_ENTERED_VALUE = (
        "//div[contains(@class,'card_one')][.//div[contains(text(),'Codes Entered')]]"
        "//div[contains(@class,'teaxt_value')]"
    )
    TOTAL_DELAY_MINS_VALUE = (
        "//div[contains(@class,'card_one')][.//div[contains(text(),'Total Delay Mins')]]"
        "//div[contains(@class,'teaxt_value')]"
    )
    SCHEDULED_STD_VALUE = (
        "//div[contains(@class,'card_one')][.//div[contains(text(),'Scheduled STD')]]"
        "//div[contains(@class,'teaxt_value')]"
    )

    # Table & Details below in Popup 
    DELAY_TABLE_CONTAINER = ".delay-table-container"
    DELAY_TABLE = ".delay-table"
    DELAY_TABLE_ROWS = ".delay-table tbody tr:not(.remark-row):not([class*='remark'])"
    DELAY_DURATION_INPUT = "td.delay-duration-input input, input.input_field, input[type='number']"
    NO_DATA_MESSAGE = ".noData"

    # Action Buttons
    CANCEL_BUTTON = ".footer-actions button:has-text('Cancel'), button:has-text('Cancel')"
    SAVE_BUTTON = ".footer-actions button:has-text('Save'), button:has-text('Save')"

    # Loading Spinners
    SPINNER_SELECTORS = [
        ".loading",
        ".spinner",
        ".mat-progress-spinner",
    ]

    # ==================== CONSTRUCTOR ====================
    def __init__(self, page: Page, base_url: str | None = None):
        super().__init__(page, base_url)
        self.page = page

    # ==================== SCREENSHOT HELPER ====================
    def attach_screenshot(self, name: str, full_page: bool = True):
        """Attaches a screenshot to the Allure report."""
        try:
            try:
                screenshot = self.page.screenshot(type="jpeg", quality=65, full_page=full_page)
            except Exception:
                screenshot = self.page.screenshot(full_page=full_page)
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG
            )
            logger.info(f"Screenshot attached: {name}")
        except Exception as e:
            logger.warning(f"Failed to attach screenshot {name}: {e}")

    # ==================== LOADING HELPER ====================
    def wait_for_loading_to_finish(self, timeout: int = 30000):
        """Waits for any active loading spinners to disappear."""
        try:
            for selector in self.SPINNER_SELECTORS:
                spinners = self.page.locator(selector)
                for index in range(spinners.count()):
                    spinner = spinners.nth(index)
                    if spinner.is_visible():
                        expect(spinner).not_to_be_visible(timeout=timeout)
            logger.info("Loading completed successfully")
        except TimeoutError:
            self.attach_screenshot("spinner_timeout")
            logger.warning(f"Loading spinner did not disappear within {timeout} ms")

    # ==================== NAVIGATION ====================
    @allure.step("Navigate to Flights List View")
    def navigate_to_list_view_page(self):
        """Navigates to the Flights List View dashboard."""
        logger.info("Navigating to Flights List View")
        try:
            if self.page.locator(self.DEPARTED_TAB).is_visible():
                logger.info("Already on Flights List View dashboard")
                return

            menu = self.page.locator(self.MENU)
            expect(menu.first).to_be_visible(timeout=30000)
            menu.first.hover()
            self.page.wait_for_timeout(1000)

            flights = self.page.locator(self.FLIGHTS)
            if not flights.first.is_visible():
                logger.warning("Flights item not visible after hover, clicking menu")
                menu.first.click()
                self.page.wait_for_timeout(1000)

            expect(flights.first).to_be_visible(timeout=15000)
            flights.first.click()
            logger.info("Clicked Flights List View")

            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(2000)
            self.wait_for_loading_to_finish()
            logger.info("Flights List View loaded successfully")
        except Exception as e:
            self.attach_screenshot("navigate_list_view_failed")
            logger.error(f"Failed to navigate to Flights List View: {e}")
            raise

    # ==================== SELECT DEPARTED SECTION ====================
    @allure.step("Select Departed Section")
    def select_departed_flights(self):
        try:
            departed_tab = self.page.locator(self.DEPARTED_TAB)
            expect(departed_tab.first).to_be_visible(timeout=15000)
            departed_tab.first.click()
            logger.info("Clicked Departed tab")

            self.page.wait_for_timeout(3000)
            self.wait_for_loading_to_finish()

            flight_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            if flight_cards.count() > 0:
                expect(flight_cards.first).to_be_visible(timeout=15000)
                logger.info(f"Departed flights loaded. Found {flight_cards.count()} flight cards")
            else:
                logger.warning("No departed flight cards found on page")

        except Exception as e:
            self.attach_screenshot("select_departed_failed")
            logger.error(f"Failed to select Departed section: {e}")
            raise

    # ==================== DELAY CODE ICON INSPECTION ====================
    def is_delay_code_icon_green(self, flight_card: Locator) -> tuple[bool, Locator | None]:
        """
        Inspects the Delay Code icon on a flight card.
        Returns:
            (True, icon_locator) if the icon is present and green.
            (False, icon_locator_or_None) if the icon is not green or not present.
        """
        delay_icon = flight_card.locator(self.DELAY_CODE_ICON)
        if delay_icon.count() == 0 or not delay_icon.first.is_visible():
            return False, None

        icon_element = delay_icon.first
        class_attr = icon_element.get_attribute("class") or ""

        if "addeddelaycode" in class_attr:
            logger.info("Delay code icon has class 'addeddelaycode' (Green)")
            return True, icon_element

        if "green" in class_attr.lower():
            logger.info(f"Delay code icon has green in class attribute: {class_attr}")
            return True, icon_element

        try:
            color = icon_element.evaluate("el => window.getComputedStyle(el).color")
            match = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color)
            if match:
                r, g, b = map(int, match.groups())
                if g > 100 and g > r * 1.1 and g > b * 1.1:
                    logger.info(f"Delay code icon computed color is green: {color}")
                    return True, icon_element
        except Exception as e:
            logger.debug(f"Computed color check exception: {e}")

        return False, icon_element

    def get_flight_number(self, flight_card: Locator) -> str:
        try:
            flight_num_loc = flight_card.locator(self.FLIGHT_NUMBER)
            if flight_num_loc.count() > 0 and flight_num_loc.first.is_visible():
                return flight_num_loc.first.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    # ==================== POPUP ACTIONS ====================
    @allure.step("Open Delay Codes Popup")
    def open_delay_code_popup(self, icon_element: Locator) -> Locator:
        logger.info("Clicking Green Delay Code icon")
        icon_element.click()
        self.page.wait_for_timeout(2000)

        popup = self.page.locator(self.DELAY_POPUP).first
        expect(popup).to_be_visible(timeout=15000)
        logger.info("Delay Codes Popup opened successfully")
        return popup

    @allure.step("Validate Delay Codes Count and Delay Minutes")
    def validate_delay_codes_and_minutes(self, popup: Locator, flight_label: str):
       
        logger.info(f"Validating Delay Codes popup for {flight_label}")
        self.attach_screenshot(f"delay_codes_popup_{flight_label}")

        codes_entered_loc = popup.locator(self.CODES_ENTERED_VALUE)
        expect(codes_entered_loc.first).to_be_visible(timeout=10000)
        codes_entered_text = codes_entered_loc.first.inner_text().strip()
        codes_entered_match = re.search(r"\d+", codes_entered_text)
        codes_entered = int(codes_entered_match.group(0)) if codes_entered_match else 0
        logger.info(f"[{flight_label}] Summary Codes Entered: {codes_entered}")

        total_mins_loc = popup.locator(self.TOTAL_DELAY_MINS_VALUE)
        expect(total_mins_loc.first).to_be_visible(timeout=10000)
        total_mins_text = total_mins_loc.first.inner_text().strip()
        total_mins_match = re.search(r"\d+", total_mins_text)
        total_delay_mins = int(total_mins_match.group(0)) if total_mins_match else 0
        logger.info(f"[{flight_label}] Summary Total Delay Mins: {total_delay_mins}")

        header_delay_loc = popup.locator(self.HEADER_DELAY_MINS)
        if header_delay_loc.count() > 0 and header_delay_loc.first.is_visible():
            header_text = header_delay_loc.first.inner_text().strip()
            logger.info(f"[{flight_label}] Header Delay Text: '{header_text}'")

        raw_table_rows = popup.locator(self.DELAY_TABLE_ROWS)

        delay_code_rows = []
        for r in range(raw_table_rows.count()):
            row = raw_table_rows.nth(r)
            row_class = row.get_attribute("class") or ""
            if "remark" in row_class.lower():
                continue
            if row.locator("td[colspan]").count() > 0 or row.locator(".remark-box, .remarks_text_area, textarea#remarkInput").count() > 0:
                continue
            delay_code_rows.append(row)

        table_rows_count = len(delay_code_rows)
        logger.info(f"[{flight_label}] Delay code rows count below (excluding remarks rows): {table_rows_count}")

        # Verification 1: Verify Codes Entered matches number of rows below 
        assert table_rows_count == codes_entered, (
            f"[{flight_label}] Mismatch in Delay Codes Count: "
            f"Summary shows {codes_entered} codes entered, but table below has {table_rows_count} delay code rows (excluding remark rows)!"
        )
        logger.info(
            f"[{flight_label}] SUCCESS: Delay codes count matched! "
            f"Summary ({codes_entered}) == Table Rows ({table_rows_count})"
        )

        # Verification 2: Verify Total Delay Mins matches sum of minutes from table rows
        calculated_total_mins = 0
        for r, row in enumerate(delay_code_rows):
            duration_input = row.locator(self.DELAY_DURATION_INPUT)
            if duration_input.count() > 0 and duration_input.first.is_visible():
                row_val_str = duration_input.first.input_value().strip()
            else:
                cells = row.locator("td")
                row_val_str = cells.nth(3).inner_text().strip() if cells.count() > 3 else "0"

            val_match = re.search(r"\d+", row_val_str)
            row_duration = int(val_match.group(0)) if val_match else 0

            code_col = row.locator("td").first.inner_text().strip() if row.locator("td").count() > 0 else f"Row {r+1}"
            logger.info(f"[{flight_label}] Delay Code Row {r + 1} ({code_col}): {row_duration} mins")
            calculated_total_mins += row_duration

        logger.info(
            f"[{flight_label}] Calculated Table Sum: {calculated_total_mins} mins | "
            f"Summary Value: {total_delay_mins} mins"
        )

        assert calculated_total_mins == total_delay_mins, (
            f"[{flight_label}] Mismatch in Delay Minutes: "
            f"Summary shows {total_delay_mins} mins, but table rows sum to {calculated_total_mins} mins!"
        )
        logger.info(
            f"[{flight_label}] SUCCESS: Delay minutes matched! "
            f"Summary ({total_delay_mins} mins) == Table Sum ({calculated_total_mins} mins)"
        )

    @allure.step("Close Delay Codes Popup")
    def close_delay_code_popup(self, popup: Locator):
        """Closes the Delay Codes popup via Cancel button."""
        logger.info("Closing Delay Codes Popup")
        cancel_btn = popup.locator(self.CANCEL_BUTTON).first
        if cancel_btn.is_visible():
            cancel_btn.click()
            self.page.wait_for_timeout(500)

        expect(popup).not_to_be_visible(timeout=10000)
        logger.info("Delay Codes Popup closed successfully")

    # ==================== MAIN WORKFLOW ====================
    @allure.step("Validate Departed Flights Delay Codes")
    def validate_departed_delay_codes(self, max_flights: int | None = None):
        """
        Iterates over departed flight cards:
        - If the Delay Code icon is green:
            Clicks on it, verifies codes entered and delay minutes match table below, closes popup.
        - If the Delay Code icon is NOT green:
            Leaves / skips that flight as instructed.
        """
        flight_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
        total_flights = flight_cards.count()

        if total_flights == 0:
            logger.warning("No flight cards found in Departed section")
            return

        flights_to_check = total_flights if max_flights is None else min(total_flights, max_flights)
        logger.info(f"Checking {flights_to_check} of {total_flights} Departed flight cards")

        green_flights_count = 0
        skipped_flights_count = 0

        for i in range(flights_to_check):
            flight_card = flight_cards.nth(i)
            flight_card.scroll_into_view_if_needed()
            flight_label = self.get_flight_number(flight_card)

            logger.info(f"--- Flight {i + 1}/{flights_to_check}: {flight_label} ---")

            is_green, icon_element = self.is_delay_code_icon_green(flight_card)

            if not is_green or icon_element is None:
                logger.info(f"Flight {i + 1} ({flight_label}): Delay Code icon is NOT green. Leaving this flight.")
                skipped_flights_count += 1
                continue

            logger.info(f"Flight {i + 1} ({flight_label}): Delay Code icon IS green! Clicking to inspect delay codes...")
            green_flights_count += 1

            popup = self.open_delay_code_popup(icon_element)
            try:
                self.validate_delay_codes_and_minutes(popup, flight_label)
            finally:
                self.close_delay_code_popup(popup)

            logger.info(f"Flight {i + 1} ({flight_label}): Validation completed successfully")

        logger.info(
            f"Departed Delay Codes validation finished. "
            f"Total inspected: {flights_to_check}, Green icon flights validated: {green_flights_count}, "
            f"Skipped (non-green): {skipped_flights_count}"
        )



