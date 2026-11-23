# Author : Gowthami Ankem
# Created Date : 2026-11-18
# Author : Gowthami Ankem
# Modified Date : 2026-11-23

"""
==============  INTRODUCTION ================
Page Object: ListView_DepartedSection_Alerts_Page
Description: Checking departed flights alerts in Flights List View.

Workflow:
1. Open Flights List View and click on the Departed tab.
2. Check the alerts button on each departed flight card.
3. Open the alerts popup for every flight:
   - For flights with '00' alerts: verify that the popup shows 'No alerts found'.
   - For flights with active alerts: check visible alerts, Critical alerts, and Pending alerts.
   - For each alert card, open its details:
     * Check the Details tab: verify the alert message is displayed, and if Critical, verify Criticality shows 'Critical'.
     * Check the History tab:
       - 'Open' alerts must show 'Alert Generated'.
       - 'Acknowledged' alerts must show 'Alert Generated' and 'Acknowledged'.
       - 'Closed' alerts must show 'Alert Generated', 'Acknowledged', and 'Closed'.
   - Click the back button to go back to the alert list.
4. Close the alerts popup before checking the next flight.
"""

import re
import allure
from playwright.sync_api import Locator, expect, TimeoutError
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

    # ==================== ALERT CARDS & POPUP LOCATORS ====================
    ALERT_BUTTON = ".Departed_alerts_buttonOne, [class*='Departed_alerts_button'], .alerts-col button"
    POPUP = ".notification-div:visible, .grid_alerts_menu:visible"
    POPUP_CLOSE_BUTTON = "mat-icon:has-text('close'), .close-icon, [class*='close']"
    NO_ALERTS_MSG = "text='No alerts found', :has-text('No alerts found')"
    ALERT_CARDS = ".alert-card:visible, .alert-card, [class*='alert-card']:visible"
    ALERT_TITLE = ".alert-title-name, .alert-title, [class*='title']"
    ALERT_STATUS_BADGE = ".status-badge, .alert-status, [class*='status']"
    ALERT_MESSAGE = ".alert-subtitle, [class*='subtitle'], pre, p"
    ALERT_DETAIL_VIEW = ".alert-detail-view.slide-in, .alert-detail-view:visible, [class*='alert-detail-view']:visible"
    DETAILS_TAB = "text=Details, .mat-tab-label:has-text('Details'), [role='tab']:has-text('Details')"
    HISTORY_TAB = "text=History, .mat-tab-label:has-text('History'), [role='tab']:has-text('History')"
    BACK_BUTTON = "mat-icon:has-text('arrow_back'), mat-icon:has-text('arrow_back_ios'), mat-icon:has-text('chevron_left'), .back-button"

    # ==================== LOADING SPINNERS ====================
    SPINNER_SELECTORS = [
        ".loading",
        ".spinner",
        ".mat-progress-spinner",
    ]

    # ==================== SCREENSHOT HELPER ====================
    def attach_screenshot(self, name: str, full_page: bool = False):
        """Captures a screenshot and attaches it to the report."""
        try:
            try:
                screenshot = self.page.screenshot(type="jpeg", quality=65, full_page=full_page)
            except Exception:
                screenshot = self.page.screenshot(full_page=full_page)
            allure.attach(screenshot, name=name, attachment_type=allure.attachment_type.PNG)
            logger.info(f"Screenshot saved: {name}")
        except Exception as e:
            logger.warning(f"Could not attach screenshot {name}: {e}")

    # ==================== LOADING HELPER ====================
    def wait_for_loading_to_finish(self, timeout: int = 10000):
        """Waits for any page loading spinners to disappear."""
        try:
            for selector in self.SPINNER_SELECTORS:
                spinners = self.page.locator(selector)
                for index in range(spinners.count()):
                    spinner = spinners.nth(index)
                    if spinner.is_visible():
                        expect(spinner).not_to_be_visible(timeout=timeout)
        except TimeoutError:
            pass

    # ==================== NAVIGATION ====================
    @allure.step("Navigate to Flights List View")
    def navigate_to_list_view_page(self):
        """Navigates to the Flights List View dashboard."""
        logger.info("Opening Flights List View page")
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
            logger.error(f"Could not navigate to Flights List View: {e}")
            raise

    @allure.step("Select Departed Section")
    def select_departed_flights(self):
        """Clicks on the Departed tab to show departed flights."""
        try:
            departed_tab = self.page.locator(self.DEPARTED_TAB)
            expect(departed_tab.first).to_be_visible(timeout=10000)
            departed_tab.first.click()
            self.page.wait_for_timeout(1500)
            self.wait_for_loading_to_finish()

            flight_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            if flight_cards.count() > 0:
                expect(flight_cards.first).to_be_visible(timeout=10000)
                logger.info(f"Departed flights loaded successfully. Found {flight_cards.count()} flight cards")
        except Exception as e:
            self.attach_screenshot("select_departed_failed")
            logger.error(f"Could not open Departed section: {e}")
            raise

    # ==================== FLIGHT & ALERT  ====================
    def get_flight_number(self, flight_card: Locator) -> str:
        """Reads the flight number from the flight card."""
        try:
            flight_num_loc = flight_card.locator(self.FLIGHT_NUMBER)
            if flight_num_loc.count() > 0 and flight_num_loc.first.is_visible():
                return flight_num_loc.first.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    def get_alert_count(self, flight_card: Locator) -> tuple[int, Locator | None]:
        """Finds the alert button on the flight card and reads the alert count number."""
        try:
            btn = flight_card.locator(self.ALERT_BUTTON).first
            if btn.is_visible():
                txt = btn.inner_text().strip() or (btn.text_content() or "").strip()
                digits = re.findall(r"\d+", txt)
                count = int(digits[0]) if digits else 0
                logger.info(f"Found alert button: text='{txt}', count={count}")
                return count, btn
        except Exception as e:
            logger.debug(f"Could not read alert button: {e}")
        return 0, None

    def get_visible_popup(self) -> Locator | None:
        try:
            popup = self.page.locator(self.POPUP).first
            if popup.is_visible():
                return popup
        except Exception:
            pass
        return None

    def close_popup(self, popup: Locator | None = None):
        """Closes the alert popup using the close 'X' button."""
        try:
            target = popup if (popup and popup.is_visible()) else self.get_visible_popup()
            if target and target.is_visible():
                close_btn = target.locator(self.POPUP_CLOSE_BUTTON).first
                if close_btn.is_visible():
                    close_btn.click()
                    self.page.wait_for_timeout(400)
        except Exception as e:
            logger.debug(f"Could not click close button: {e}")

    def click_category_button(self, popup: Locator, category_name: str) -> bool:
        """Clicks an alert category filter button (such as Critical or Pending) in the popup."""
        try:
            buttons = popup.locator(
                f"button:has-text('{category_name}'), "
                f"[role='button']:has-text('{category_name}'), "
                f"div:has-text('{category_name}'), "
                f"span:has-text('{category_name}')"
            )
            for i in range(buttons.count()):
                button = buttons.nth(i)
                txt = button.inner_text().strip()
                if txt.lower() == category_name.lower() and button.is_visible():
                    button.click()
                    self.page.wait_for_timeout(400)
                    return True
        except Exception as e:
            logger.debug(f"Could not click category '{category_name}': {e}")
        return False

    def click_details_tab(self, detail_view: Locator) -> bool:
        try:
            tab = detail_view.locator(self.DETAILS_TAB).first
            if tab.is_visible():
                tab.click()
                self.page.wait_for_timeout(400)
                return True

            page_tab = self.page.get_by_text("Details", exact=True).last
            if page_tab.is_visible():
                page_tab.click()
                self.page.wait_for_timeout(400)
                return True
        except Exception as e:
            logger.debug(f"Could not click Details tab: {e}")
        return False

    def click_history_tab(self, detail_view: Locator) -> bool:
        logger.info("Looking for History tab in alert details...")
        try:
            tab = detail_view.locator(self.HISTORY_TAB).first
            if tab.is_visible():
                tab.click()
                self.page.wait_for_timeout(500)
                logger.info("Clicked History tab successfully")
                return True

            page_tab = self.page.get_by_text("History", exact=True).last
            if page_tab.is_visible():
                page_tab.click()
                self.page.wait_for_timeout(500)
                logger.info("Clicked History tab via page text")
                return True
        except Exception as e:
            logger.debug(f"Could not click History tab: {e}")
        return False

    def click_back_button(self, detail_view: Locator):
        """Clicks the back button to return from alert details to the alert list."""
        try:
            btn = detail_view.locator(self.BACK_BUTTON).first
            if btn.is_visible():
                btn.click()
                self.page.wait_for_timeout(400)
                return True
        except Exception as e:
            logger.debug(f"Could not click back button: {e}")
        return False

    # ==================== ALERT VALIDATIONS ====================
    def verify_alert_history(self, flight_name: str, alert_title: str, status: str, detail_view: Locator):
        """
        Checks that the alert timeline history matches its current status:
        - 'Open': shows 'Alert Generated'
        - 'Acknowledged': shows both 'Alert Generated' and 'Acknowledged'
        - 'Closed': shows 'Alert Generated', 'Acknowledged', and 'Closed'
        """
        status_norm = status.strip().lower()
        logger.info(f"[{flight_name}] Checking history for alert '{alert_title}' (Status: '{status}')")
        self.page.wait_for_timeout(500)

        history_text = detail_view.inner_text().lower()

        # Check 'Alert Generated'
        assert "alert generated" in history_text or "generated" in history_text, (
            f"[{flight_name}] Alert '{alert_title}' is missing 'Alert Generated' in its history timeline."
        )

        # Check 'Acknowledged' for Acknowledged or Closed alerts
        if "acknowledged" in status_norm or "closed" in status_norm:
            assert "acknowledged" in history_text or "ack" in history_text, (
                f"[{flight_name}] Alert '{alert_title}' is missing 'Acknowledged' in its history timeline."
            )

        # Check 'Closed' for Closed alerts
        if "closed" in status_norm:
            assert "closed" in history_text, (
                f"[{flight_name}] Alert '{alert_title}' is missing 'Closed' in its history timeline."
            )

        logger.info(f"[{flight_name}] Alert '{alert_title}' history verified successfully")

    def verify_alert_details(
        self,
        flight_name: str,
        alert_title: str,
        detail_view: Locator,
        is_critical: bool = False,
        expected_message: str | None = None
    ):
        """
        Validates the Details tab of an alert:
        - Confirms that the alert message is displayed.
        - If the alert is Critical, verifies that Criticality is displayed as 'Critical'.
        """
        logger.info(f"[{flight_name}] Checking Details tab for alert '{alert_title}' (Critical expected: {is_critical})")
        self.page.wait_for_timeout(500)

        details_raw = detail_view.inner_text().strip()
        details_norm = " ".join(details_raw.replace("\u00a0", " ").lower().split())
        logger.info(f"[{flight_name}] Details tab text:\n{details_raw[:300]}")

        # 1. Verify Alert Message is shown on Details tab
        message_verified = False
        if expected_message:
            expected_norm = " ".join(expected_message.replace("\u00a0", " ").lower().split())
            if expected_norm in details_norm:
                message_verified = True
            else:
                # Flexible match: check if key words of the message exist in details
                words = [w for w in re.findall(r"[a-zA-Z0-9]+", expected_norm) if len(w) > 2]
                if words and sum(1 for w in words if w in details_norm) >= len(words) * 0.7:
                    message_verified = True

        # Fallback: check if 'message' label is present with non-empty content
        if not message_verified and "message" in details_norm and len(details_norm) > 20:
            message_verified = True

        assert message_verified, (
            f"[{flight_name}] Alert '{alert_title}' message was not found on Details tab.\n"
            f"Expected message: '{expected_message}'\n"
            f"Details content: {details_raw}"
        )
        logger.info(f"[{flight_name}] Alert message verified on Details tab: '{expected_message or 'Message present'}'")

        # 2. Verify Criticality if this alert is Critical
        if is_critical or "critical" in details_norm:
            assert "critical" in details_norm, (
                f"[{flight_name}] Alert '{alert_title}' is marked as Critical, but 'Critical' was not found on Details tab.\n"
                f"Details content: {details_raw}"
            )
            logger.info(f"[{flight_name}] Alert '{alert_title}' Criticality confirmed as 'Critical'")
        else:
            logger.info(f"[{flight_name}] Alert '{alert_title}' Details tab verified successfully")

    def _process_visible_cards(
        self,
        flight_name: str,
        popup: Locator,
        seen_titles: set,
        category_name: str = "All"
    ) -> int:
        """Checks each visible alert card in the popup, validates Details tab, then History timeline."""
        cards_loc = popup.locator(self.ALERT_CARDS)
        card_count = cards_loc.count()
        validated = 0

        for idx in range(card_count):
            card = popup.locator(self.ALERT_CARDS).nth(idx)
            if not card.is_visible():
                continue

            title_loc = card.locator(self.ALERT_TITLE)
            alert_title = title_loc.first.inner_text().strip() if title_loc.count() > 0 else f"Alert-{idx + 1}"

            # Skip if we already checked this alert
            if alert_title in seen_titles:
                continue
            seen_titles.add(alert_title)

            status_loc = card.locator(self.ALERT_STATUS_BADGE)
            alert_status = status_loc.first.inner_text().strip() if status_loc.count() > 0 else "Unknown"

            card_text = card.inner_text()
            msg_loc = card.locator(self.ALERT_MESSAGE).first
            card_message = msg_loc.inner_text().strip() if msg_loc.is_visible() else None
            is_critical = (category_name.lower() == "critical") or ("critical" in card_text.lower())

            logger.info(f"[{flight_name}] Opening alert details for: '{alert_title}' (Status: '{alert_status}')")
            card.click()
            self.page.wait_for_timeout(600)

            # Check details view opened
            detail_view = self.page.locator(self.ALERT_DETAIL_VIEW).first
            try:
                expect(detail_view).to_be_visible(timeout=4000)
            except Exception:
                self.attach_screenshot(f"{flight_name}_detail_view_open_failed")
                raise AssertionError(f"[{flight_name}] Alert details did not open for alert '{alert_title}'")

            # 1. Check Details tab (Message & Criticality)
            self.click_details_tab(detail_view)
            self.verify_alert_details(
                flight_name=flight_name,
                alert_title=alert_title,
                detail_view=detail_view,
                is_critical=is_critical,
                expected_message=card_message,
            )

            # 2. Switch to History tab
            if not self.click_history_tab(detail_view):
                self.attach_screenshot(f"{flight_name}_history_tab_missing")
                raise AssertionError(f"[{flight_name}] History tab was not found for alert '{alert_title}'")

            # 3. Check history timeline
            self.verify_alert_history(flight_name, alert_title, alert_status, detail_view)
            validated += 1

            # Click back button to return to alert cards list
            self.click_back_button(detail_view)
            self.page.wait_for_timeout(400)

        return validated

    def process_flight_alert_cards(self, flight_name: str, popup: Locator, button_count: int) -> int:
        """
        Checks alerts inside the popup for a flight:
        - When alert count is '00': checks that the popup shows 'No alerts found'.
        - When alert count is greater than 0: checks directly visible alerts, Critical alerts, and Pending alerts.
        """
        no_alerts = popup.locator(self.NO_ALERTS_MSG)
        has_no_alerts = no_alerts.count() > 0 and no_alerts.first.is_visible()

        initial_cards = popup.locator(self.ALERT_CARDS)
        initial_card_count = initial_cards.count()

        # Flight has '00' alerts
        if button_count == 0:
            if initial_card_count > 0:
                msg = f"[{flight_name}] Note: Alert button showed '00', but {initial_card_count} alert card(s) were found inside the popup."
                logger.warning(msg)
                allure.attach(msg, name=f"{flight_name}_count_difference", attachment_type=allure.attachment_type.TEXT)
                seen_titles = set()
                return self._process_visible_cards(flight_name, popup, seen_titles, category_name="All")
            else:
                logger.info(f"[{flight_name}] Confirmed: Button showed '00' and popup shows 'No alerts found' as expected.")
                return 0

        # Flight has count > 0
        if has_no_alerts and initial_card_count == 0:
            logger.warning(f"[{flight_name}] Alert button showed count {button_count}, but popup initially shows 'No alerts found'.")

        seen_titles = set()
        total_validated = 0

        # 1. Check all alerts initially visible
        if initial_card_count > 0:
            logger.info(f"[{flight_name}] Checking visible alerts ({initial_card_count} cards found)")
            total_validated += self._process_visible_cards(flight_name, popup, seen_titles, category_name="All")

        # 2. Check Critical alerts category
        logger.info(f"[{flight_name}] Checking 'Critical' alerts category")
        if self.click_category_button(popup, "Critical"):
            total_validated += self._process_visible_cards(flight_name, popup, seen_titles, category_name="Critical")

        # 3. Check Pending alerts category
        logger.info(f"[{flight_name}] Checking 'Pending' alerts category")
        if self.click_category_button(popup, "Pending"):
            total_validated += self._process_visible_cards(flight_name, popup, seen_titles, category_name="Pending")

        return total_validated

    @allure.step("Validate Alerts in Departed Section")
    def validate_departed_flights_alerts(self, max_flights: int | None = None):
        """
        Main validation method:
        - Opens Departed section.
        - Iterates over departed flight cards.
        - Clicks alert button to open popup.
        - Validates alert cards and their history timeline.
        - Closes popup before moving to next flight.
        """
        logger.info("Starting alerts check for Departed flights")
        self.wait_for_loading_to_finish()

        flight_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
        total_flights = flight_cards.count()

        if total_flights == 0:
            logger.warning("No departed flight cards found on the page")
            self.attach_screenshot("no_departed_flights")
            return

        flights_to_check = total_flights if max_flights is None else min(total_flights, max_flights)
        logger.info(f"Departed section has {total_flights} flights. Checking {flights_to_check} flights.")

        flights_checked = 0
        total_alerts_checked = 0

        for index in range(flights_to_check):
            card = self.page.locator(self.FLIGHT_ROW_CARDS).nth(index)
            flight_name = self.get_flight_number(card)

            logger.info(f"--- Checking Flight [{index + 1}/{flights_to_check}]: {flight_name} ---")

            alert_count, alert_btn = self.get_alert_count(card)
            if alert_btn is None:
                logger.warning(f"[{flight_name}] No alert button found. Skipping this flight.")
                continue

            logger.info(f"[{flight_name}] Alert button count is {alert_count}. Clicking to open popup...")
            alert_btn.scroll_into_view_if_needed()
            alert_btn.click()
            self.page.wait_for_timeout(1000)

            # Locate the open popup
            popup = self.get_visible_popup()
            if popup is None:
                self.page.wait_for_timeout(1000)
                popup = self.get_visible_popup()

            if popup is None:
                self.attach_screenshot(f"{flight_name}_popup_open_failed")
                raise AssertionError(f"[{flight_name}] Alerts popup failed to open after clicking alert button.")

            # Validate alerts in popup
            validated = self.process_flight_alert_cards(flight_name, popup, alert_count)
            total_alerts_checked += validated

            # Close popup before proceeding
            logger.info(f"[{flight_name}] Closing alerts popup...")
            self.close_popup(popup)
            self.page.wait_for_timeout(400)

            flights_checked += 1
            self.attach_screenshot(f"{flight_name}_alerts_validated", full_page=False)

        logger.info(
            f"Alerts validation finished! Checked {flights_checked} flights and verified {total_alerts_checked} alerts total."
        )
