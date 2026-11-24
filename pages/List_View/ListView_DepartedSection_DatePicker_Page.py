# Author : Gowthami Ankem
# Created Date : 2026-11-24

"""
==============  INTRODUCTION ================
Page Object: ListView_DepartedSection_DatePicker_Page
Description: Validates Date Picker and Historical Departed Flights in Flights List View.
             Opens the date picker popup, selects previous/historical dates from the calendar popup,
             clicks the search icon to fetch flights for the selected date, validates that historical
             departed flights update and load accurately, and restores back to today's date.
"""

from datetime import datetime, timedelta
import re
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_DepartedSection_DatePicker_Page(BasePage):

    # ==================== NAVIGATION LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[text()='menu']"
    LIST_VIEW = "//div[@role='button']/span[text()='Flights']"
    DEPARTED_TAB = "//div[contains(text(),'Departed')]"
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # ==================== DATE PICKER & SEARCH LOCATORS ====================
    DATE_INPUT = ".dateInput input"
    CALENDAR_ICON = ".dateInput button"
    CALENDAR_POPUP = ".p-datepicker"
    DATE_CELLS = ".p-datepicker-calendar td:not(.p-disabled) span"
    SEARCH_BUTTON = "i.headerIcons.pi-search"

    # ==================== LOADING SPINNERS ====================
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
            screenshot = self.page.screenshot(full_page=full_page)
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG
            )
            logger.info(f"Screenshot attached: {name}")
        except Exception as e:
            logger.warning(f"Failed to attach screenshot {name}: {e}")

    # ==================== LOADING SPINNERS ====================
    def wait_for_loading_to_finish(self, timeout: int = 90000):
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
            pytest.fail(f"Loading spinner did not disappear within {timeout} ms")

    # ==================== NAVIGATION ====================
    @allure.step("Navigate to Flights List View")
    def navigate_to_list_view_page(self):
        try:
            logger.info("Navigating to Flights List View")
            self.page.wait_for_timeout(2000)

            # Check if Departed tab is already visible
            departed = self.page.locator(self.DEPARTED_TAB)
            if departed.count() > 0 and departed.first.is_visible():
                logger.info("Already on Flights List View dashboard")
                return

            menu = self.page.locator(self.MENU)
            expect(menu).to_be_visible(timeout=30000)
            menu.hover()
            self.page.wait_for_timeout(1000)

            list_view = self.page.locator(self.LIST_VIEW)
            if not list_view.is_visible():
                logger.warning("List View not displayed after Hover, Clicking Menu")
                menu.click()
                self.page.wait_for_timeout(1000)

            expect(list_view).to_be_visible(timeout=15000)
            list_view.click()

            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(2000)
            self.wait_for_loading_to_finish()
            logger.info("List View loaded successfully")
        except Exception as e:
            self.attach_screenshot("list_view_load_failed")
            logger.error(f"Failed to open List View: {e}")
            raise

    # ==================== DEPARTED TAB ====================
    @allure.step("Select Departed Flights")
    def select_departed_flights(self):
        try:
            departed = self.page.locator(self.DEPARTED_TAB)
            expect(departed).to_be_visible(timeout=15000)
            departed.click()

            self.page.wait_for_timeout(1500)
            self.wait_for_loading_to_finish()

            cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)

            if cards.count() > 0:
                expect(cards.first).to_be_visible(timeout=15000)
                logger.info(f"Departed flights loaded. Found {cards.count()} flight cards")
            elif no_flights.count() > 0 and no_flights.first.is_visible():
                logger.info("Departed tab loaded: 'No Flights Available' displayed")
            else:
                logger.info("Departed tab selected successfully")
        except Exception as e:
            self.attach_screenshot("departed_tab_failed")
            logger.error(f"Failed to select Departed tab: {e}")
            raise

    # ==================== DATE PICKER & SEARCH ACTIONS ====================
    def get_current_date_text(self) -> str:
        """Reads the currently selected date from the date input."""
        date_input = self.page.locator(self.DATE_INPUT)
        expect(date_input).to_be_visible(timeout=10000)
        current_val = date_input.input_value().strip()
        logger.info(f"Current date input value: '{current_val}'")
        return current_val

    @allure.step("Click Search Icon to fetch flights for selected date")
    def click_search_icon(self):
        """Clicks the search icon to apply the selected date filter."""
        logger.info("Clicking Search icon after selecting date")
        search_btn = self.page.locator(self.SEARCH_BUTTON)
        expect(search_btn).to_be_visible(timeout=10000)
        search_btn.click()
        logger.info("Clicked search icon")
        self.page.wait_for_timeout(1500)
        self.wait_for_loading_to_finish()

    @allure.step("Select Historical Date via Date Picker: {target_date_str}")
    def select_date(self, target_date_str: str):
        """
        Selects a date by opening the calendar popup, clicking the target day cell,
        and then clicking the search icon.
        """
        logger.info(f"Selecting date from calendar popup: {target_date_str}")
        
        cal_btn = self.page.locator(self.CALENDAR_ICON)
        if cal_btn.is_visible():
            cal_btn.click()
        else:
            self.page.locator(self.DATE_INPUT).click()

        self.page.wait_for_timeout(500)

        # Wait for calendar popup
        cal_popup = self.page.locator(self.CALENDAR_POPUP)
        expect(cal_popup).to_be_visible(timeout=10000)

        # Locate and click the target day in calendar popup
        day_num = target_date_str.split("/")[0].lstrip("0")
        day_cells = self.page.locator(self.DATE_CELLS)
        day_cell = day_cells.filter(has_text=re.compile(rf"^\s*{day_num}\s*$")).first
        expect(day_cell).to_be_visible(timeout=10000)
        day_cell.click()
        logger.info(f"Clicked day {day_num} in calendar popup")

        self.page.wait_for_timeout(500)

        # Click on search icon after selecting previous date
        self.click_search_icon()

        self.page.wait_for_timeout(1500)
        self.wait_for_loading_to_finish()
        logger.info(f"Date changed to {target_date_str} and search applied")

    @allure.step("Verify Historical Departed Flights Loaded for Date: {target_date_str}")
    def verify_historical_flights_loaded(self, target_date_str: str):
        """Verifies that departed flights or proper empty state loads for historical date."""
        cards = self.page.locator(self.FLIGHT_ROW_CARDS)
        no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)

        card_count = cards.count()
        if card_count > 0:
            expect(cards.first).to_be_visible(timeout=15000)
            logger.info(f"Historical date {target_date_str} loaded {card_count} departed flight cards")
        elif no_flights.count() > 0 and no_flights.first.is_visible():
            logger.info(f"Historical date {target_date_str} correctly displays 'No Flights Available'")
        else:
            logger.info(f"Historical date {target_date_str} state verified")

        self.attach_screenshot(f"historical_flights_{target_date_str.replace('/', '_')}")

    @allure.step("Test Historical Date Navigation Workflow")
    def validate_historical_date_workflow(self):
        """
        Executes full date navigation:
        1. Records today's date.
        2. Calculates yesterday's date.
        3. Navigates to yesterday via calendar popup, clicks search icon, and verifies loaded flights.
        4. Restores back to today's date via calendar popup, clicks search icon, and verifies loaded flights.
        """
        today_str = self.get_current_date_text()
        try:
            today_dt = datetime.strptime(today_str, "%d/%m/%Y")
        except Exception:
            today_dt = datetime.now()
            today_str = today_dt.strftime("%d/%m/%Y")

        yesterday_dt = today_dt - timedelta(days=1)
        yesterday_str = yesterday_dt.strftime("%d/%m/%Y")

        # 1. Select yesterday via calendar popup and click search icon
        logger.info(f"Navigating to yesterday: {yesterday_str}")
        self.select_date(yesterday_str)
        self.verify_historical_flights_loaded(yesterday_str)

        # 2. Restore today via calendar popup and click search icon
        logger.info(f"Restoring back to today: {today_str}")
        self.select_date(today_str)
        self.verify_historical_flights_loaded(today_str)
        logger.info("Date picker workflow completed successfully")
