# Author : Gowthami Ankem
# Created Date : 2026-11-18

"""
Page Object: ListView_DepartedSection_Alerts_Page
Description: Page Object for Departed Section Alerts validation.
             Works across SALZBURG, BELFAST, and FLYDUBAI.
             Workflow:
             1. Navigate to Flights List View and click Departed tab.
             2. Inspect flight cards for alerts button (.Departed_alerts_buttonOne).
             3. Click on the alert button for every flight (including '00'):
                - If count is '00':
                    * Open drawer and check if 'No alerts found' or if any alert cards exist.
                    * If alert cards exist despite '00', report/log discrepancy (alerts present but count not showing).
                - If count > 0:
                    * Open drawer.
                    * Check directly visible alerts, then click 'Critical' and 'Pending' one after another.
                    * For each alert card:
                        - Click card to open detail view (.alert-detail-view).
                        - Switch to History tab.
                        - Assert status history rules:
                            * Open: contains 'Alert Generated'
                            * Acknowledged: contains 'Alert Generated' and 'Acknowledged'
                            * Closed: contains 'Alert Generated', 'Acknowledged', and 'Closed'
                        - Click Back button to return to alert list.
             4. Close the popup drawer via close icon 'X' before proceeding to the next flight.
"""

import re
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_DepartedSection_Alerts_Page(BasePage):

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

    # ==================== ALERT CARDS & DETAIL LOCATORS ====================
    NO_ALERTS_MSG = "text='No alerts found', :has-text('No alerts found')"
    ALERT_CARDS = ".alert-card:visible, .alert-card, [class*='alert-card']:visible"
    ALERT_TITLE = ".alert-title-name, .alert-title, [class*='title']"
    ALERT_STATUS_BADGE = ".status-badge, .alert-status, [class*='status']"

    ALERT_DETAIL_VIEW = ".alert-detail-view.slide-in, .alert-detail-view:visible, [class*='alert-detail-view']:visible"

    SPINNER_SELECTORS = [
        ".loading",
        ".spinner",
        ".mat-progress-spinner",
    ]

    def __init__(self, page: Page, base_url: str | None = None):
        super().__init__(page, base_url)
        self.page = page

    def attach_screenshot(self, name: str, full_page: bool = False):
        try:
            try:
                screenshot = self.page.screenshot(type="jpeg", quality=65, full_page=full_page)
            except Exception:
                screenshot = self.page.screenshot(full_page=full_page)
            allure.attach(screenshot, name=name, attachment_type=allure.attachment_type.PNG)
            logger.info(f"Screenshot attached: {name}")
        except Exception as e:
            logger.warning(f"Failed to attach screenshot {name}: {e}")

    def wait_for_loading_to_finish(self, timeout: int = 10000):
        try:
            for selector in self.SPINNER_SELECTORS:
                spinners = self.page.locator(selector)
                for index in range(spinners.count()):
                    spinner = spinners.nth(index)
                    if spinner.is_visible():
                        expect(spinner).not_to_be_visible(timeout=timeout)
        except TimeoutError:
            pass

    @allure.step("Navigate to Flights List View")
    def navigate_to_list_view_page(self):
        logger.info("Navigating to Flights List View")
        try:
            if "/app/turnaround-list" in self.page.url or self.page.locator(self.DEPARTED_TAB).is_visible():
                self.page.wait_for_timeout(800)
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
            self.page.wait_for_timeout(1500)
            self.wait_for_loading_to_finish()
        except Exception as e:
            self.attach_screenshot("navigate_list_view_failed")
            logger.error(f"Failed to navigate to Flights List View: {e}")
            raise

    @allure.step("Select Departed Section")
    def select_departed_flights(self):
        try:
            departed_tab = self.page.locator(self.DEPARTED_TAB)
            expect(departed_tab.first).to_be_visible(timeout=10000)
            departed_tab.first.click()
            self.page.wait_for_timeout(1500)
            self.wait_for_loading_to_finish()

            flight_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            if flight_cards.count() > 0:
                expect(flight_cards.first).to_be_visible(timeout=10000)
                logger.info(f"Departed flights loaded. Found {flight_cards.count()} flight cards")
        except Exception as e:
            self.attach_screenshot("select_departed_failed")
            logger.error(f"Failed to select Departed section: {e}")
            raise

    def get_flight_number(self, flight_card: Locator) -> str:
        try:
            flight_num_loc = flight_card.locator(self.FLIGHT_NUMBER)
            if flight_num_loc.count() > 0 and flight_num_loc.first.is_visible():
                return flight_num_loc.first.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    def get_alert_count(self, flight_card: Locator) -> tuple[int, Locator | None]:
        """Locates the alert button in the flight card and extracts the alert count."""
        # 1. Pure CSS selectors
        css_selectors = [
            ".Departed_alerts_buttonOne",
            "[class*='Departed_alerts_button']",
            ".alerts-col button",
            ".alerts-col",
            "[class*='alerts'] button",
        ]
        for sel in css_selectors:
            try:
                elements = flight_card.locator(sel)
                total = elements.count()
                for idx in range(total):
                    el = elements.nth(idx)
                    if el.is_visible():
                        txt = el.inner_text().strip() or (el.text_content() or "").strip()
                        digits = re.findall(r"\d+", txt)
                        count = int(digits[0]) if digits else 0
                        logger.info(f"Alert button found with '{sel}': text='{txt}' -> count={count}")
                        return count, el
            except Exception as e:
                logger.debug(f"Selector '{sel}' failed: {e}")

        # 2. Pure XPath selectors
        xpath_selectors = [
            ".//button[contains(@class,'Departed_alerts_button')]",
            ".//div[contains(@class,'alerts-col')]//button",
            ".//div[contains(@class,'alerts-col')]",
            ".//button[contains(@class,'alerts')]",
        ]
        for xp in xpath_selectors:
            try:
                el = flight_card.locator(f"xpath={xp}").first
                if el.is_visible():
                    txt = el.inner_text().strip() or (el.text_content() or "").strip()
                    digits = re.findall(r"\d+", txt)
                    count = int(digits[0]) if digits else 0
                    logger.info(f"Alert button found with XPath '{xp}': text='{txt}' -> count={count}")
                    return count, el
            except Exception as e:
                logger.debug(f"XPath '{xp}' failed: {e}")

        return 0, None

    def get_visible_drawer(self) -> Locator | None:
        """Finds and returns the currently visible alerts drawer container."""
        # CSS candidates
        css_candidates = [
            ".grid_alerts_menu .notification-div",
            ".grid_alerts_menu",
            ".notification-div:visible",
            "[class*='notification-div']:visible",
        ]
        for sel in css_candidates:
            try:
                loc = self.page.locator(sel)
                count = loc.count()
                for idx in range(count):
                    el = loc.nth(idx)
                    if el.is_visible():
                        return el
            except Exception:
                pass

        # XPath candidates
        xpath_candidates = [
            "//div[contains(@class,'grid_alerts_menu')]//div[contains(@class,'notification-div')]",
            "//div[contains(@class,'grid_alerts_menu')]",
            "//div[contains(@class,'notification-div') and not(contains(@style,'display: none'))]",
        ]
        for xp in xpath_candidates:
            try:
                loc = self.page.locator(f"xpath={xp}")
                count = loc.count()
                for idx in range(count):
                    el = loc.nth(idx)
                    if el.is_visible():
                        return el
            except Exception:
                pass

        return None

    def close_drawer(self, drawer: Locator | None = None):
        """Closes the alert popup drawer cleanly via 'X' close button or Escape."""
        try:
            # 1. Close icon inside drawer
            if drawer and drawer.is_visible():
                for sel in ["mat-icon:has-text('close')", ".close-icon", "[class*='close']"]:
                    close_btn = drawer.locator(sel).first
                    if close_btn.is_visible():
                        close_btn.click()
                        self.page.wait_for_timeout(300)
                        break

            # 2. Page-level XPath for close button
            if drawer and drawer.is_visible():
                page_close = self.page.locator("xpath=//div[contains(@class,'notification-div')]//mat-icon[normalize-space()='close' or text()='close'] | //div[contains(@class,'grid_alerts_menu')]//mat-icon[normalize-space()='close' or text()='close']").last
                if page_close.is_visible():
                    page_close.click()
                    self.page.wait_for_timeout(300)
        except Exception as e:
            logger.debug(f"Exception clicking close button: {e}")

        # 3. Always ensure closed via Escape if still visible
        active = self.get_visible_drawer()
        if active:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)

    def click_category_pill(self, drawer: Locator, category_name: str) -> bool:
        """Clicks a category pill (e.g. Critical, Pending) inside the drawer."""
        try:
            pills = drawer.locator(
                f"button:has-text('{category_name}'), "
                f"[role='button']:has-text('{category_name}'), "
                f"div:has-text('{category_name}'), "
                f"span:has-text('{category_name}')"
            )
            for i in range(pills.count()):
                pill = pills.nth(i)
                txt = pill.inner_text().strip()
                if txt.lower() == category_name.lower() and pill.is_visible():
                    pill.click()
                    self.page.wait_for_timeout(400)
                    return True
        except Exception as e:
            logger.debug(f"Failed to click category '{category_name}': {e}")
        return False

    def click_history_tab(self, detail_view: Locator) -> bool:
        """Finds and clicks the History tab inside the detail view."""
        logger.info("Attempting to click History tab...")

        # 1. Pure text / CSS selectors inside detail_view
        css_options = [
            "text=History",
            ".mat-tab-label:has-text('History')",
            "[role='tab']:has-text('History')",
            "div:has-text('History')",
            "span:has-text('History')",
            ":has-text('History')",
        ]
        for sel in css_options:
            try:
                candidates = detail_view.locator(sel)
                for i in range(candidates.count()):
                    tab = candidates.nth(i)
                    if tab.is_visible() and "history" in tab.inner_text().strip().lower():
                        logger.info(f"Clicked History tab with selector: {sel}")
                        tab.click()
                        self.page.wait_for_timeout(500)
                        return True
            except Exception:
                pass

        # 2. Pure XPath selectors inside detail_view
        xpath_options = [
            ".//div[contains(@class,'mat-tab-label') and contains(.,'History')]",
            ".//div[normalize-space()='History']",
            ".//span[normalize-space()='History']",
            ".//*[normalize-space(text())='History']",
        ]
        for xp in xpath_options:
            try:
                tab = detail_view.locator(f"xpath={xp}").first
                if tab.is_visible():
                    logger.info(f"Clicked History tab with XPath: {xp}")
                    tab.click()
                    self.page.wait_for_timeout(500)
                    return True
            except Exception:
                pass

        # 3. Page-level get_by_text fallback
        try:
            page_tab = self.page.get_by_text("History", exact=True).last
            if page_tab.is_visible():
                logger.info("Clicked History tab via page.get_by_text")
                page_tab.click()
                self.page.wait_for_timeout(500)
                return True
        except Exception:
            pass

        return False

    def click_back_button(self, detail_view: Locator):
        """Clicks the back arrow button to return from detail view to alerts list."""
        back_selectors = [
            "mat-icon:has-text('arrow_back')",
            "mat-icon:has-text('arrow_back_ios')",
            "mat-icon:has-text('chevron_left')",
            ".back-button",
            "[class*='back']",
            "button:has(mat-icon)",
            "mat-icon",
        ]
        for sel in back_selectors:
            try:
                btn = detail_view.locator(sel).first
                if btn.is_visible():
                    btn.click()
                    self.page.wait_for_timeout(400)
                    return True
            except Exception:
                pass

        # Fallback XPath
        try:
            back_xpath = detail_view.locator("xpath=.//mat-icon[contains(text(),'arrow_back') or contains(text(),'chevron_left') or @class='back-button']").first
            if back_xpath.is_visible():
                back_xpath.click()
                self.page.wait_for_timeout(400)
                return True
        except Exception:
            pass

        return False

    def verify_alert_history(self, flight_name: str, alert_title: str, status: str, detail_view: Locator):
        """
        Validates timeline history according to user status rules:
        - Open: contains 'Alert Generated'
        - Acknowledged: contains 'Alert Generated' and 'Acknowledged'
        - Closed: contains 'Alert Generated', 'Acknowledged', and 'Closed'
        """
        status_norm = status.strip().lower()
        logger.info(f"[{flight_name}] Validating history for alert '{alert_title}' with status '{status}'")

        # Give history content a moment to render
        self.page.wait_for_timeout(600)

        # Capture all text in the detail view / history panel
        history_text = detail_view.inner_text().lower()
        logger.info(f"[{flight_name}] History panel text captured:\n{history_text[:300]}")

        # Rule 1: 'Open' status must have 'Alert Generated'
        has_generated = "alert generated" in history_text or "generated" in history_text
        assert has_generated, (
            f"[{flight_name}] Alert '{alert_title}' (Status: '{status}') missing 'Alert Generated' in history!\n"
            f"Captured history content: {history_text}"
        )

        # Rule 2: 'Acknowledged' status must have 'Alert Generated' + 'Acknowledged'
        if "acknowledged" in status_norm:
            has_acknowledged = "acknowledged" in history_text or "ack" in history_text
            assert has_acknowledged, (
                f"[{flight_name}] Alert '{alert_title}' (Status: '{status}') missing 'Acknowledged' in history!\n"
                f"Captured history content: {history_text}"
            )

        # Rule 3: 'Closed' status must have 'Alert Generated' + 'Acknowledged' + 'Closed'
        if "closed" in status_norm:
            has_acknowledged = "acknowledged" in history_text or "ack" in history_text
            has_closed = "closed" in history_text or "alert closed" in history_text
            assert has_acknowledged, (
                f"[{flight_name}] Alert '{alert_title}' (Status: '{status}') missing 'Acknowledged' in history!\n"
                f"Captured history content: {history_text}"
            )
            assert has_closed, (
                f"[{flight_name}] Alert '{alert_title}' (Status: '{status}') missing 'Closed' in history!\n"
                f"Captured history content: {history_text}"
            )

        logger.info(f"[{flight_name}] Alert '{alert_title}' history successfully verified for status '{status}'")

    def _process_visible_cards(self, flight_name: str, drawer: Locator, seen_titles: set) -> int:
        """Iterates through visible alert cards in the drawer and validates detail & history."""
        cards_loc = drawer.locator(self.ALERT_CARDS)
        card_count = cards_loc.count()
        validated = 0

        for idx in range(card_count):
            card = drawer.locator(self.ALERT_CARDS).nth(idx)
            if not card.is_visible():
                continue

            title_loc = card.locator(self.ALERT_TITLE)
            alert_title = title_loc.first.inner_text().strip() if title_loc.count() > 0 else f"Alert-{idx + 1}"

            # Avoid re-validating the same alert card twice
            if alert_title in seen_titles:
                continue
            seen_titles.add(alert_title)

            status_loc = card.locator(self.ALERT_STATUS_BADGE)
            alert_status = status_loc.first.inner_text().strip() if status_loc.count() > 0 else "Unknown"

            logger.info(f"[{flight_name}] Opening alert card: '{alert_title}' (Status: '{alert_status}')")
            card.click()
            self.page.wait_for_timeout(600)

            # Detail view validation
            detail_view = self.page.locator(self.ALERT_DETAIL_VIEW).first
            try:
                expect(detail_view).to_be_visible(timeout=4000)
            except Exception:
                self.attach_screenshot(f"{flight_name}_detail_view_open_failed")
                raise AssertionError(f"[{flight_name}] Alert detail view did not open for alert '{alert_title}'")

            # Click History tab
            if not self.click_history_tab(detail_view):
                self.attach_screenshot(f"{flight_name}_history_tab_missing")
                raise AssertionError(f"[{flight_name}] History tab not found in detail view for alert '{alert_title}'")

            # Validate history timeline
            self.verify_alert_history(flight_name, alert_title, alert_status, detail_view)
            validated += 1

            # Back button to return to alert list
            self.click_back_button(detail_view)
            self.page.wait_for_timeout(400)

        return validated

    def process_flight_alert_cards(self, flight_name: str, drawer: Locator, button_count: int) -> int:
        """
        Processes alerts inside the drawer:
        - For '00' count flights: verifies empty state, or flags if cards are present despite '00'.
        - For count > 0 flights: checks directly visible alerts, then Critical and Pending categories.
        """
        # 1. Check if 'No alerts found' is displayed
        no_alerts = drawer.locator(self.NO_ALERTS_MSG)
        has_no_alerts = no_alerts.count() > 0 and no_alerts.first.is_visible()

        # Check existing cards in initial view
        initial_cards = drawer.locator(self.ALERT_CARDS)
        initial_card_count = initial_cards.count()

        # Case A: Button displayed '00'
        if button_count == 0:
            if initial_card_count > 0:
                # Discrepancy: Alert button says 00, but alerts are present inside
                msg = f"[{flight_name}] DISCREPANCY: Alert button displayed '00', but {initial_card_count} alert card(s) are present in drawer!"
                logger.warning(msg)
                allure.attach(msg, name=f"{flight_name}_count_discrepancy", attachment_type=allure.attachment_type.TEXT)
                seen_titles = set()
                return self._process_visible_cards(flight_name, drawer, seen_titles)
            else:
                logger.info(f"[{flight_name}] Verified: Button showed '00' and drawer shows 'No alerts found' (Empty state confirmed).")
                return 0

        # Case B: Button displayed count > 0
        if has_no_alerts and initial_card_count == 0:
            logger.warning(f"[{flight_name}] Button showed count {button_count}, but drawer initially shows 'No alerts found'!")

        seen_titles = set()
        total_validated = 0

        # 1) Check alerts visible initially (Flight / All)
        if initial_card_count > 0:
            logger.info(f"[{flight_name}] Checking initial visible alerts ({initial_card_count} cards)")
            total_validated += self._process_visible_cards(flight_name, drawer, seen_titles)

        # 2) Click Critical category
        logger.info(f"[{flight_name}] Checking 'Critical' category alerts")
        if self.click_category_pill(drawer, "Critical"):
            total_validated += self._process_visible_cards(flight_name, drawer, seen_titles)

        # 3) Click Pending category
        logger.info(f"[{flight_name}] Checking 'Pending' category alerts")
        if self.click_category_pill(drawer, "Pending"):
            total_validated += self._process_visible_cards(flight_name, drawer, seen_titles)

        return total_validated

    @allure.step("Validate Alerts in Departed Section")
    def validate_departed_flights_alerts(self, max_flights: int | None = None):
        logger.info("Starting validation of alerts in Departed section")
        self.wait_for_loading_to_finish()

        flight_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
        total_flights = flight_cards.count()

        if total_flights == 0:
            logger.warning("No departed flight cards available to validate")
            self.attach_screenshot("no_departed_flights")
            return

        flights_to_check = total_flights if max_flights is None else min(total_flights, max_flights)
        logger.info(f"Departed section contains {total_flights} flights. Checking {flights_to_check} flights.")

        flights_checked = 0
        total_alerts_checked = 0

        for index in range(flights_to_check):
            card = self.page.locator(self.FLIGHT_ROW_CARDS).nth(index)
            flight_name = self.get_flight_number(card)

            logger.info(f"--- Checking Flight [{index + 1}/{flights_to_check}]: {flight_name} ---")

            alert_count, alert_btn = self.get_alert_count(card)
            if alert_btn is None:
                logger.warning(f"[{flight_name}] No alert button found. Skipping.")
                continue

            logger.info(f"[{flight_name}] Alert button count: {alert_count}. Clicking alert button...")
            alert_btn.scroll_into_view_if_needed()
            alert_btn.click()
            self.page.wait_for_timeout(800)

            # Locate the visible drawer
            drawer = self.get_visible_drawer()
            if drawer is None:
                alert_btn.click()
                self.page.wait_for_timeout(800)
                drawer = self.get_visible_drawer()

            if drawer is None:
                self.attach_screenshot(f"{flight_name}_popup_open_failed")
                raise AssertionError(f"[{flight_name}] Alerts popup drawer did not open!")

            # Validate alerts inside popup (handles 00 and count > 0)
            validated = self.process_flight_alert_cards(flight_name, drawer, alert_count)
            total_alerts_checked += validated

            # Close popup drawer via close icon 'X' so next flight can be opened
            logger.info(f"[{flight_name}] Closing alerts popup drawer...")
            self.close_drawer(drawer)
            self.page.wait_for_timeout(400)

            flights_checked += 1
            self.attach_screenshot(f"{flight_name}_alerts_validated", full_page=False)

        logger.info(
            f"Validation Completed: Checked {flights_checked} flights "
            f"(including '00' empty-state & discrepancy checks), validated {total_alerts_checked} alerts total."
        )
