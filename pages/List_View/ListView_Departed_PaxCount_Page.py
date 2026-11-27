# Author : Gowthami Ankem
# Created Date : 2026-11-24

"""
==============  INTRODUCTION ================
Page Object: ListView_Departed_PaxCount_Page
Description: Validates Passenger (PAX) Count and Breakdown popup in Departed Section of Flights List View.
         
"""

import re
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Departed_PaxCount_Page(BasePage):

    # ==================== NAVIGATION LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[text()='menu']"
    LIST_VIEW = "//div[@role='button']/span[text()='Flights']"
    DEPARTED_TAB = "//div[contains(text(),'Departed')]"
    FLIGHTS_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # ==================== PAX LOCATORS (from Flights_List_View_Pax_Count_Page) ====================
    ARRIVAL_AND_DEPARTURE_NUMBER = "//p[@mattooltip='Flight Arrival Departure Numbers']"
    ARRIVAL_AND_DEPARTURE_PAX = "//div[contains(@class,'pax_count-col')]/div[@class='dropdown']/div[@class='dropbtn']"
    PAX_COUNT_POPUP = "//div[contains(@class,'pax_count-col')]/div[@class='dropdown']/div[@class='dropdown-content']"

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

            departed = self.page.locator(self.DEPARTED_TAB)
            if departed.count() > 0 and departed.first.is_visible():
                logger.info("Already on Flights List View dashboard")
                return

            menu = self.page.locator(self.MENU)
            expect(menu.first).to_be_visible(timeout=30000)
            menu.first.hover()
            self.page.wait_for_timeout(1000)

            list_view = self.page.locator(self.LIST_VIEW)
            if not list_view.first.is_visible():
                logger.warning("List View not displayed after Hover, Clicking Menu")
                menu.first.click()
                self.page.wait_for_timeout(1000)

            expect(list_view.first).to_be_visible(timeout=15000)
            list_view.first.click()

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
            expect(departed.first).to_be_visible(timeout=15000)
            departed.first.click()

            self.page.wait_for_timeout(1500)
            self.wait_for_loading_to_finish()

            cards = self.page.locator(self.FLIGHTS_CARDS)
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

    # ==================== FLIGHT COUNT ====================
    def count_of_flights(self) -> int:
        """Counts the number of flight cards in Departed section."""
        flights = self.page.locator(self.FLIGHTS_CARDS)
        if flights.count() == 0:
            return 0
        expect(flights.first).to_be_visible()
        count = flights.count()
        logger.info(f"Totally we have {count} Departed Flights")
        return count

    # ==================== FLIGHT NUMBER ====================
    def arrival_and_departure_number(self, flight: Locator):
        """Reads Arrival and Departure flight numbers from card."""
        try:
            with allure.step("Check Arrival and Departure Number"):
                arr_and_dep = flight.locator(self.ARRIVAL_AND_DEPARTURE_NUMBER)
                expect(arr_and_dep.first).to_be_visible()
                flight_number = arr_and_dep.first.inner_text().split('-')
                arrival_number = flight_number[0].strip()
                departure_number = flight_number[1].strip() if len(flight_number) > 1 else ""
                logger.info(f"Arrival Number = {arrival_number} & Departure Number = {departure_number}")
                return arrival_number, departure_number
        except Exception as e:
            logger.warning(f"Could not read arrival/departure number: {e}")
            return "Unknown", "Unknown"

    # ==================== CARD PAX EXTRACTION ====================
    def arrival_and_departure_pax(self, flight: Locator):
        """Reads Arrival and Departure PAX count from flight card."""
        try:
            with allure.step("Check Arrival and Departure PAX Count"):
                total_pax = flight.locator(self.ARRIVAL_AND_DEPARTURE_PAX)
                expect(total_pax.first).to_be_visible()
                pax_text = total_pax.first.inner_text()
                pax_count = pax_text.split("|")
                arrival_pax_count = pax_count[0].strip()
                departure_pax_count = pax_count[1].strip() if len(pax_count) > 1 else ""
                logger.info(f"Arrival PAX Count = {arrival_pax_count} & Departure PAX Count = {departure_pax_count}")
                return arrival_pax_count, departure_pax_count, total_pax.first
        except Exception as e:
            logger.warning(f"Failed to extract PAX from card: {e}")
            raise

    # ==================== SEGREGATION VALIDATION ====================
    def validate_pax_count_from_segregation(self, flight: Locator, popup_text: str, arrival_pax_count: str, departure_pax_count: str):
        """Cross-checks popup segregation numbers (J, Y, Infant) against card values."""
        # Verify sections
        assert "Arrival" in popup_text, "Arrival section not found in popup"
        assert "Departure" in popup_text, "Departure section not found in popup"

        # Extract Arrival values
        arrival_match = re.search(
            r"Arrival\s*J:\s*(\d+)\s*Y:\s*(\d+)\s*Infant:\s*(\d+)",
            popup_text,
            re.DOTALL
        )

        # Extract Departure values
        departure_match = re.search(
            r"Departure\s*J:\s*(\d+)\s*Y:\s*(\d+)\s*Infant:\s*(\d+)",
            popup_text,
            re.DOTALL
        )

        if not arrival_match:
            pytest.fail("Arrival segregation values not found")

        if not departure_match:
            pytest.fail("Departure segregation values not found")

        arrival_j = int(arrival_match.group(1))
        arrival_y = int(arrival_match.group(2))
        arrival_infant = int(arrival_match.group(3))

        departure_j = int(departure_match.group(1))
        departure_y = int(departure_match.group(2))
        departure_infant = int(departure_match.group(3))

        logger.info(f"Arrival -> J:{arrival_j}, Y:{arrival_y}, Infant:{arrival_infant}")
        logger.info(f"Departure -> J:{departure_j}, Y:{departure_y}, Infant:{departure_infant}")

        # Calculate totals
        arrival_total = arrival_j + arrival_y
        departure_total = departure_j + departure_y

        logger.info(f"Calculated Arrival Total = {arrival_total}")
        logger.info(f"Calculated Departure Total = {departure_total}")

        # Compare against values already extracted from card
        if arrival_pax_count and arrival_pax_count != '-':
            assert int(arrival_total) == int(arrival_pax_count), (
                f"Arrival mismatch: Card={arrival_pax_count}, Popup={arrival_total}"
            )

        if departure_pax_count and departure_pax_count != '-':
            assert int(departure_total) == int(departure_pax_count), (
                f"Departure mismatch: Card={departure_pax_count}, Popup={departure_total}"
            )

        logger.info("Arrival and Departure PAX segregation validated successfully")

    # ==================== CHECK SEGREGATION POPUP ====================
    def check_segregation_of_pax(self, flight: Locator, arrival_pax_count: str, departure_pax_count: str):
        """Hovers on PAX count, captures popup text, validates segregation, and moves away."""
        pax_count = flight.locator(self.ARRIVAL_AND_DEPARTURE_PAX)
        expect(pax_count.first).to_be_visible()

        try:
            pax_count.first.hover(timeout=3000)
        except Exception:
            pax_count.first.hover(force=True)
            pax_count.first.dispatch_event("mouseenter")

        self.page.wait_for_timeout(800)

        pax_count_popup = flight.locator(self.PAX_COUNT_POPUP)
        expect(pax_count_popup.first).to_be_visible()

        popup_text = pax_count_popup.first.inner_text().strip()
        logger.info(f"PAX Count Popup Text:\n{popup_text}")
        self.attach_screenshot("pax_segregation_popup")

        self.validate_pax_count_from_segregation(flight, popup_text, arrival_pax_count, departure_pax_count)

        # Move mouse away to body to dismiss hover popup
        self.page.locator("body").hover()
        self.page.wait_for_timeout(400)

    # ==================== VALIDATE DEPARTED FLIGHTS ====================
    @allure.step("Validate PAX Count across Departed Flights")
    def validate_departed_pax_counts(self, max_flights: int | None = None) -> int:
        """Iterates through departed flights and validates PAX counts and segregation."""
        self.wait_for_loading_to_finish()
        number_of_flights = self.count_of_flights()

        if number_of_flights == 0:
            logger.warning("No Departed Flights Found")
            return 0

        flights_to_check = min(number_of_flights, max_flights) if max_flights else min(number_of_flights, 15)
        logger.info(f"Validating PAX for {flights_to_check} Departed flights")

        validated = 0
        failed_flights = []

        for i in range(flights_to_check):
            logger.info(f"============================== Departed Flight {i + 1}/{flights_to_check} ==============================")
            flight = self.page.locator(self.FLIGHTS_CARDS).nth(i)
            flight.scroll_into_view_if_needed()

            try:
                arrival_number, departure_number = self.arrival_and_departure_number(flight)
                arrival_pax_count, departure_pax_count, total_pax = self.arrival_and_departure_pax(flight)

                logger.info(f"Flight {arrival_number} - {departure_number}: Arrival PAX = {arrival_pax_count}, Departure PAX = {departure_pax_count}")

                if arrival_pax_count and arrival_pax_count != '-':
                    arr_val = int(arrival_pax_count)
                    if arr_val >= 185:
                        logger.warning(f"Arrival PAX is {arr_val} (>= 185)")

                if departure_pax_count and departure_pax_count != '-':
                    dep_val = int(departure_pax_count)
                    if dep_val >= 185:
                        logger.warning(f"Departure PAX is {dep_val} (>= 185)")

                logger.info(f"Validating PAX segregation popup for Flight {arrival_number} - {departure_number}")
                self.check_segregation_of_pax(flight, arrival_pax_count, departure_pax_count)
                validated += 1

            except Exception as e:
                logger.error(f"Flight Iteration {i + 1} Failed: {e}")
                self.attach_screenshot(f"pax_failure_flight_{i + 1}")
                failed_flights.append(f"Flight {i + 1}: {e}")

        if failed_flights:
            logger.warning(f"Some flights had PAX validation failures: {failed_flights}")

        logger.info(f"PAX count validation completed for {validated} departed flights")
        return validated
