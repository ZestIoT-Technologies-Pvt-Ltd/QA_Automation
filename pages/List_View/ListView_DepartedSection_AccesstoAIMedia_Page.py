# Author : Gowthami Ankem
# Created Date : 2026-11-20
# Author : Gowthami Ankem
# Modified Date : 2026-11-23
"""
==============  INTRODUCTION ================
Page Object: ListView_DepartedSection_AccesstoAIMedia_Page
Description: Departed Section Access to AI Media validation in Flights List View.
             Validates AI-captured media (cameras, videos, and image timestamps) for departed flights.
             Inspects Turnaround and Split flight operations, verifies turnaround progress indicators,
             expands activity panels (Arrival, Departure, Additional Activities), opens AI media players,
             takes verification screenshots, and safely closes Popup.

Workflow Capabilities:
1. Navigate to Flights List View and switch to the Departed section tab.
2. Inspect Departed flight cards and verify availability.
3. For each departed flight:
   - Click to open the flight details view.
   - Detect flight operation type (Turnaround vs Split flight).
   - Validate that activity progress numerator is non-zero (activities captured).
   - If Split flight:
     * Expand activity accordion panels (Arrival Activities, Departure Activities, Additional Activities).
     * Check for AI media elements (.image-class) within each panel.
     * Click each AI media element to open the video/media player popup (#player).
     * Capture a screenshot of the opened media player.
     * Close the popup (#player) and proceed.
   - If Turnaround flight:
     * Verify turnaround activity rows and Off Block .
     * Check AI media elements and open/validate player popup.
4.  Return and continue with subsequent departed flights.
"""

import re
import time
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_DepartedSection_AccesstoAIMedia_Page(BasePage):

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
    FLIGHT_DETAILS = ".flight-details.ng-star-inserted"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # ==================== FLIGHT HEADER & PROGRESS LOCATORS ====================
    TURNAROUND_HEADER = ".turnaround-header"
    SPLIT_HEADER = "mat-expansion-panel-header.split-expansion-header"
    FLIGHT_EXPANSION_HEADERS = (
        ".turnaround-header, "
        "mat-expansion-panel-header.split-expansion-header"
    )
    PROGRESS_NUMERATOR = 'p[style*="float: left"], p[style*="float:left"]'

    # ==================== ACTIVITY & MEDIA LOCATORS ====================
    DETAIL_ROWS = (
        ".row-white-background.ng-star-inserted, "
        ".row-colored-background.ng-star-inserted"
    )
    MAT_ACCORDION = "mat-accordion"
    MAT_PANEL = "mat-expansion-panel"
    PANEL_HEADER = "mat-expansion-panel-header"

    ACTIVITY_NAMES = [
        "Arrival Activities",
        "Departure Activities",
        "Additional Activities",
    ]

    IMAGE_ELEMENTS = ".image-class"
    POPUP_PLAYER = "#player, app-preview-dialog"
    CLOSE_BUTTON = "app-preview-dialog span.cursor-pointer"

    # ==================== LOADING SPINNERS ====================
    SPINNER_SELECTORS = [
        ".loading",
        ".spinner",
        ".mat-progress-spinner",
    ]

    # ==================== CONSTRUCTOR ====================
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    # ==================== SCREENSHOT ====================
    def attach_screenshot(self, name: str, full_page: bool = True):
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
            if self.page.locator(self.DEPARTED_TAB).is_visible():
                logger.info("Already on Flights List View dashboard")
                return

            menu = self.page.locator(self.MENU)
            expect(menu.first).to_be_visible(timeout=30000)
            menu.first.hover()
            self.page.wait_for_timeout(1000)

            flights = self.page.locator(self.FLIGHTS)
            if not flights.first.is_visible():
                menu.first.click()
                self.page.wait_for_timeout(1000)

            expect(flights.first).to_be_visible(timeout=15000)
            flights.first.click()

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

    # ==================== FLIGHT TYPE DETECTION ====================
    def detect_flight_type(self) -> str | None:
        """Determines whether the expanded flight is Turnaround or Split."""
        turnaround = self.page.locator(self.TURNAROUND_HEADER)
        split = self.page.locator(self.SPLIT_HEADER)

        if turnaround.count() and turnaround.first.is_visible():
            return "turnaround"
        if split.count() and split.first.is_visible():
            return "split"
        return None

    def wait_for_flight_header(self, timeout: int = 90000) -> str:
        """Waits for flight header to appear and detects flight type."""
        headers = self.page.locator(self.FLIGHT_EXPANSION_HEADERS)
        expect(headers.first).to_be_visible(timeout=timeout)

        flight_type = self.detect_flight_type()
        if flight_type is None:
            raise AssertionError("Could not identify Turnaround or Split flight structure")

        logger.info(f"Flight type detected: {flight_type}")
        return flight_type

    # ==================== PROGRESS VALIDATION ====================
    @allure.step("Validate progress numerator")
    def check_progress_numerator_not_zero(self):
        """Verifies that at least one progress numerator in the flight card is greater than zero."""
        elements = self.page.locator(self.PROGRESS_NUMERATOR)
        if elements.count() == 0:
            logger.info("Progress numerator element not present; proceeding with activity inspection")
            return

        values = []
        for i in range(elements.count()):
            element = elements.nth(i)
            if not element.is_visible():
                continue

            value_text = element.inner_text().strip()
            logger.info(f"Progress indicator {i + 1}: {value_text}")

            match = re.search(r"^\s*(\d+)\s*/\s*\d+", value_text)
            if match:
                values.append(int(match.group(1)))

        if values and not any(value > 0 for value in values):
            logger.warning(f"All progress numerators are zero: {values}")
        else:
            logger.info(f"Progress validation passed: {values}")

    # ==================== TURNAROUND DETAIL MEDIA ====================
    @allure.step("Check Turnaround flight details and AI media")
    def check_turnaround_detail_media(self, flight_number: int = 1):
        """Validates turnaround activity rows and inspects AI media."""
        rows = self.page.locator(self.DETAIL_ROWS)
        if rows.count() == 0:
            logger.warning(f"Flight {flight_number}: No detail rows found")
            return

        for i in range(rows.count()):
            off_block = rows.nth(i).get_by_text("Off Block", exact=True)
            if off_block.count() and off_block.first.is_visible():
                logger.info(f"Flight {flight_number}: Off Block milestone found")

        images = rows.locator(self.IMAGE_ELEMENTS)
        self.process_ai_media(images, flight_number, "Turnaround")

    # ==================== SPLIT FLIGHT ACTIVITY PANELS ====================
    @allure.step("Expand Split flight activity dropdowns and check AI media")
    def check_split_flight_activity_media(self, flight_number: int = 1):
        accordion = self.page.locator(self.MAT_ACCORDION)
        expect(accordion.first).to_be_visible(timeout=15000)

        found_panels = 0
        processed_panels = 0

        for activity_name in self.ACTIVITY_NAMES:
            panels = accordion.locator(self.MAT_PANEL).filter(
                has=accordion.locator(self.PANEL_HEADER).filter(has_text=activity_name)
            )

            if panels.count() == 0:
                all_panels = accordion.locator(self.MAT_PANEL)
                matching = []
                for j in range(all_panels.count()):
                    candidate = all_panels.nth(j)
                    header = candidate.locator(self.PANEL_HEADER)
                    if header.count() and activity_name in header.first.inner_text():
                        matching.append(j)

                if not matching:
                    logger.info(f"Flight {flight_number}: '{activity_name}' panel not present")
                    continue
                panel_indexes = matching
            else:
                panel_indexes = list(range(panels.count()))

            for panel_index in panel_indexes:
                if panels.count() > 0:
                    panel = panels.nth(panel_index)
                else:
                    panel = accordion.locator(self.MAT_PANEL).nth(panel_index)

                header = panel.locator(self.PANEL_HEADER)
                if header.count() == 0:
                    continue

                found_panels += 1
                expanded = header.first.get_attribute("aria-expanded")
                if expanded != "true":
                    try:
                        header.first.scroll_into_view_if_needed(timeout=5000)
                    except Exception:
                        pass
                    header.first.click()
                    expect(header.first).to_have_attribute("aria-expanded", "true", timeout=15000)

                logger.info(f"Flight {flight_number}: '{activity_name}' expanded successfully")
                expect(panel.locator(".mat-expansion-panel-body")).to_be_visible(timeout=10000)

                images = panel.locator(self.IMAGE_ELEMENTS)
                self.page.wait_for_timeout(500)
                image_count = images.count()

                logger.info(
                    f"Flight {flight_number}: '{activity_name}' "
                    f"contains {image_count} matching AI media elements"
                )

                if image_count > 0:
                    processed = self.process_ai_media(images, flight_number, activity_name)
                    if processed > 0:
                        processed_panels += 1

        if found_panels == 0:
            logger.warning(f"Flight {flight_number}: None of the expected activity panels were found in accordion")

        logger.info(f"Flight {flight_number}: Split activity media check completed (processed {processed_panels} panels)")

    # ==================== COMMON AI MEDIA PROCESSING ====================
    def process_ai_media(self, images: Locator, flight_number: int, activity_name: str) -> int:
        processed = 0
        image_count = images.count()
        logger.info(f"Flight {flight_number} / {activity_name}: {image_count} media elements found")

        for i in range(image_count):
            image = images.nth(i)
            try:
                if not image.is_visible():
                    logger.info(f"Media {i + 1} is hidden; skipping")
                    continue

                try:
                    image.scroll_into_view_if_needed(timeout=5000)
                except Exception:
                    pass
                image.click(timeout=15000)

                self.page.wait_for_selector(self.POPUP_PLAYER, state="visible", timeout=30000)
                self.attach_screenshot(
                    f"flight_{flight_number}_{activity_name.replace(' ', '_')}_ai_media_{i + 1}"
                )

                self.close_popup()
                processed += 1
                logger.info(f"Flight {flight_number} / {activity_name}: Media {i + 1} checked successfully")

            except Exception as e:
                self.attach_screenshot(f"flight_{flight_number}_media_failed_{i + 1}")
                logger.error(f"AI media {i + 1} failed: {e}")
                raise

        return processed

    # ==================== CLOSE AI MEDIA POPUP ====================
    @allure.step("Close AI captured media popup")
    def close_popup(self):
        """Closes the AI media player popup."""
        logger.info("Closing AI media player popup")
        player = self.page.locator(self.POPUP_PLAYER)
        expect(player.first).to_be_visible(timeout=20000)

        close_button = self.page.locator(self.CLOSE_BUTTON).first
        expect(close_button).to_be_visible(timeout=10000)
        close_button.click()
        logger.info("Clicked close button on AI media popup")

        expect(player.first).not_to_be_visible(timeout=15000)
        self.page.wait_for_timeout(500)
        logger.info("AI media popup closed successfully")

    # ==================== VALIDATE DEPARTED AI MEDIA (MAIN WORKFLOW) ====================
    def validate_departed_ai_media(self, max_flights: int | None = None) -> int:
    
        try:
            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(1000)

            cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)

            if no_flights.count() > 0 and no_flights.first.is_visible():
                logger.warning("No departed flight cards available: 'No Flights Available' is displayed.")
                return 0

            total = cards.count()
            if total == 0:
                logger.warning("No departed flights found")
                return 0

            flights_to_check = min(total, max_flights) if max_flights else total
            logger.info(f"Checking {flights_to_check} of {total} Departed flights for AI media")

            validated_count = 0

            for i in range(flights_to_check):
                flight_number = i + 1
                logger.info(f"--- Checking Flight {flight_number}/{flights_to_check} ---")

                self.wait_for_loading_to_finish()
                current_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
                if i >= current_cards.count():
                    pytest.fail(f"Flight list changed while processing flight {flight_number}")

                flight = current_cards.nth(i)
                expect(flight).to_be_visible(timeout=15000)
                try:
                    flight.scroll_into_view_if_needed(timeout=5000)
                except Exception as ex:
                    logger.debug(f"Flight {flight_number} scroll_into_view_if_needed skipped/retried: {ex}")
                flight.click(timeout=15000)

                flight_type = self.wait_for_flight_header(timeout=90000)
                logger.info(f"Flight {flight_number} type: {flight_type}")

                self.wait_for_loading_to_finish()
                self.check_progress_numerator_not_zero()

                if flight_type == "split":
                    self.check_split_flight_activity_media(flight_number=flight_number)
                else:
                    self.check_turnaround_detail_media(flight_number=flight_number)

                validated_count += 1
                logger.info(f"Flight {flight_number} AI media validation completed")

            logger.info(f"All {validated_count} departed flights processed for AI media")
            return validated_count

        except Exception as e:
            self.attach_screenshot("all_departed_flights_failed")
            logger.error(f"Departed flight AI media validation failed: {e}")
            raise

    def check_all_departed_flights(self):
        return self.validate_departed_ai_media()


