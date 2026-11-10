# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: List_View_Create_Alert_Page
Description: Page Object Model for Flights List View - Creating flight-level Alert/Task functionality
             in the Ongoing section, refreshing the grid via the sync icon, and verifying alert
             presentation in the right-side details popup.

Scenario & Workflow Capabilities:
1. Navigation: Route to Flights List View dashboard via navigation menu.
2. Section Assertion: Ensure Ongoing section is active and flights are visible.
3. Alert Creation Workflow:
   - Click Three-Dots menu ('more_vert') on the flight card.
   - Select 'Add Alert/Task' menu option.
   - Enter Task Name ('Test Alert'), select Category ('Alert') from PrimeNG dropdown, select Alert Type ('Departure').
   - Save alert form and verify success toast feedback.
4. Refresh & Synchronization:
   - Click the 'Refresh Flight' (pi-sync) icon on the List View.
   - Await completion of system loading spinner.
   - Verify alert count column update.
5. Verification:
   - Click on the Alert count column to open the right-side Alert Details popup.
   - Verify the newly created alert title is listed.
   - Close the Alert Details popup.
"""

import time
import allure
from playwright.sync_api import Page, expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class List_View_Create_Alert_Page(BasePage):
    """
    Page Object for Flights List View - Creating Flight-Level Alert/Task functionality
    and verifying alert presentation in the right-side details popup.
    """

    # ==================== NAVIGATION & TOOLBAR LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    FLIGHTS = "//div[@role='button']/span[text()='Flights']"
    ONGOING_TAB = "//div[contains(text(),'Ongoing')]"
    REFRESH_FLIGHTS_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"

    # ==================== FLIGHT CARD LOCATORS ====================
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = "p[mattooltip='Flight Arrival Departure Numbers']"

    # ==================== THREE-DOTS MENU (ACTIONS COLUMN) ====================
    THREE_DOTS_MENU_ICON = "mat-icon:has-text('more_vert'), mat-icon[mattooltip='Edit Flight']"

    # Menu items inside mat-menu-content
    MENU_PANEL = "//div[contains(@class,'mat-menu-content')]"
    ADD_ALERT_TASK_MENU_ITEM = (
        "//div[contains(@class,'mat-menu-content')]//button[contains(.,'Add Alert/Task')] | "
        "//div[contains(@class,'mat-menu-content')]//span[normalize-space()='Add Alert/Task']"
    )

    # ==================== ADD ALERT / TASK DIALOG ====================
    ADD_ALERT_DIALOG = (
        "//div[contains(@class,'inputmainDiv')] | "
        "//p-dialog[.//span[contains(text(),'New Alert') or contains(text(),'Alert / Task')]] | "
        "//div[contains(@class,'p-dialog-content')]"
    )
    TASK_NAME_INPUT = "//input[@id='taskName']"
    ALERT_CATEGORY_DROPDOWN = "//p-dropdown[@id='alertCategory']"
    ALERT_CATEGORY_DROPDOWN_TRIGGER = "//p-dropdown[@id='alertCategory'] .p-dropdown-trigger"
    ALERT_CATEGORY_ITEMS = "//div[contains(@class,'p-dropdown-items-wrapper')]//li"

    CATEGORY_OPTION_ALERT = (
        "//div[contains(@class,'p-dropdown-items-wrapper')]//span[text()='Alert'] | "
        "//div[contains(@class,'p-dropdown-items-wrapper')]//li[contains(.,'Alert')]"
    )
    CATEGORY_OPTION_TASK = (
        "//div[contains(@class,'p-dropdown-items-wrapper')]//span[text()='Task'] | "
        "//div[contains(@class,'p-dropdown-items-wrapper')]//li[contains(.,'Task')]"
    )
    CATEGORY_OPTION_INCIDENT = (
        "//div[contains(@class,'p-dropdown-items-wrapper')]//span[contains(text(),'Incident')] | "
        "//div[contains(@class,'p-dropdown-items-wrapper')]//li[contains(.,'Incident')]"
    )

    # Alert Type Toggles (Arrival / Departure)
    ALERT_TYPE_ARRIVAL = (
        "//div[@class='alertTypeOptionsDiv']//h1[text()='Arrival'] | "
        "//h1[normalize-space()='Arrival']"
    )
    ALERT_TYPE_DEPARTURE = (
        "//div[@class='alertTypeOptionsDiv']//h1[text()='Departure'] | "
        "//h1[normalize-space()='Departure']"
    )

    # Save button
    ADD_ALERT_SAVE_BUTTON = (
        "//div[contains(@class,'savebuttondiv')]//h1[text()='Save'] | "
        "//div[contains(@class,'savebuttondiv')] | "
        "//button[contains(.,'Save')]"
    )

    # ==================== FALLBACK / SUCCESS MESSAGE LOCATORS ====================
    SUCCESS_SNACKBAR = "snack-bar-container, .mat-snack-bar-container, .snackbar-background"
    SUCCESS_MESSAGE_TEXT = (
        "//snack-bar-container[contains(.,'successfully') or contains(.,'Success') or contains(.,'Alert raised')] | "
        "//div[contains(@class,'mat-snack-bar-container')][contains(.,'successfully') or contains(.,'Success')] | "
        "//*[contains(@class,'snackbar-background')]"
    )

    # ==================== ALERT COLUMN ON FLIGHT CARD ====================
    ALERT_COUNT_ELEMENT = "p.alerts-list, p[class*='alerts_p'], .alerts-col p, p[class*='Ongoing_alerts_p']"
    ALERT_COL_BUTTON = "button.Ongoing_alerts_button_Two, button[class*='alerts_button'], .alerts-col button, p.alerts-list"
    ALERT_COUNT_TEXT = "p.alerts-list, p[class*='alerts_p'], .alerts-col p"

    # ==================== RIGHT-SIDE ALERT DETAILS POPUP ====================
    ALERT_DETAILS_POPUP = (
        "//div[@class='grid_alerts_menu']//div[@class='notification-div'] | "
        "//div[contains(@class,'notification-div')]"
    )
    ALERT_CARDS_IN_POPUP = (
        "//div[contains(@class,'notification-div')]//div[contains(@class,'alert-card')] | "
        "//div[@class='grid_alerts_menu']//div[contains(@class,'alert-card')]"
    )
    ALERT_TITLE_HEADER = ".//div[@class='alert-title-name'] | .//span[contains(@class,'alert-title')]"
    ALERT_SUBTITLE = ".//div[@class='alert-subtitle'] | .//pre[@class='alert-subtitle']"
    ALERT_POPUP_CLOSE_BUTTON = (
        "//div[contains(@class,'notification-div')]//mat-icon[text()='close'] | "
        "//div[@class='notification-div']//mat-icon[text()='close']"
    )

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

    # ==================== SCREENSHOT ====================
    def attach_screenshot(self, name: str, full_page: bool = True):
        """Attaches a screenshot to the Allure report."""
        try:
            screenshot = self.page.screenshot(full_page=full_page)
            allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
            logger.info(f"Screenshot attached: {name}")
        except Exception as e:
            logger.warning(f"Failed to attach screenshot {name}: {e}")

    # ==================== LOADING ====================
    def wait_for_loading_to_finish(self, timeout: int = 15000):
        """Waits for any active loading spinners to disappear."""
        try:
            for selector in self.SPINNER_SELECTORS:
                spinners = self.page.locator(selector)
                for index in range(spinners.count()):
                    spinner = spinners.nth(index)
                    if spinner.is_visible():
                        expect(spinner).not_to_be_visible(timeout=timeout)
            logger.info("Loading completed successfully")
        except Exception:
            pass

    # ==================== NAVIGATION ====================
    @allure.step("Navigate to Flights List View")
    def navigate_to_list_view_page(self):
        """Navigates from Dashboard to Flights List View via side navigation menu."""
        logger.info("Navigating to Flights List View")
        try:
            # If still on login page after fixture setup, ensure login submission completes
            if "login" in self.page.url:
                logger.info("Currently on login page; ensuring login submission completes...")
                login_btn = self.page.locator("//button[@type='submit']").first
                if login_btn.is_visible():
                    login_btn.click()
                self.page.wait_for_timeout(3000)

            menu = self.page.locator(self.MENU).first
            expect(menu).to_be_visible(timeout=30000)
            menu.hover()
            self.page.wait_for_timeout(1000)

            flights = self.page.locator(self.FLIGHTS).first
            if not flights.is_visible():
                logger.warning("Flights option not visible after hover, clicking Menu")
                menu.click()
                self.page.wait_for_timeout(1000)

            expect(flights).to_be_visible(timeout=15000)
            flights.click()
            logger.info("Clicked Flights in navigation menu")

            # Move mouse away to center so sidebar collapses
            self.page.mouse.move(600, 500)
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(2000)

            # Verify list view cards are loaded
            flights_card = self.page.locator(self.FLIGHT_ROW_CARDS)
            expect(flights_card.first).to_be_visible(timeout=30000)
            logger.info("Flights List View loaded successfully")

        except Exception as e:
            self.attach_screenshot("list_view_navigation_failed")
            logger.error(f"Failed to navigate to Flights List View: {e}")
            raise

    # ==================== SECTION HANDLING ====================
    @allure.step("Ensure Ongoing Section is selected")
    def ensure_ongoing_section(self) -> int:
        """Ensures that the Ongoing section tab is active; does not navigate away to any other section."""
        logger.info("Ensuring Ongoing section tab is active")
        try:
            # Move mouse away to ensure any opened navigation/drawer is collapsed
            self.page.mouse.move(600, 500)
            self.page.wait_for_timeout(500)

            ongoing_tab = self.page.locator(self.ONGOING_TAB).first
            expect(ongoing_tab).to_be_visible(timeout=15000)
            ongoing_tab.click(force=True)
            logger.info("Clicked Ongoing section tab")

            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(1500)

            # Confirm flights loaded
            flights = self.page.locator(self.FLIGHT_ROW_CARDS)
            expect(flights.first).to_be_visible(timeout=20000)
            count = flights.count()
            logger.info(f"Ongoing section active. Total flight cards: {count}")
            return count

        except Exception as e:
            self.attach_screenshot("ongoing_section_activation_failed")
            logger.error(f"Failed to activate Ongoing section: {e}")
            raise

    # ==================== FLIGHT CARD HELPERS ====================
    def get_flight_card_with_actions_menu(self):
        """
        Finds and returns the first flight card in the current view that has
        the Three-Dots menu available and visible (i.e. not locked/disabled).
        """
        flights = self.page.locator(self.FLIGHT_ROW_CARDS)
        total = flights.count()
        logger.info(f"Searching for an unlocked flight card with actions menu among {total} cards...")
        for i in range(total):
            card = flights.nth(i)
            three_dots = card.locator(self.THREE_DOTS_MENU_ICON).first
            if three_dots.count() > 0 and three_dots.is_visible():
                flight_num = self.get_flight_number(card)
                logger.info(f"Selected flight card #{i} ('{flight_num}') with available Three-Dots menu")
                return card

        logger.warning("No flight card found with explicitly visible Three-Dots; falling back to first card.")
        return flights.first

    def get_flight_card_by_number(self, flight_number: str):
        """
        Locates and returns the flight card matching the given flight_number.
        If not found by exact text, matches flight number tokens or returns the first available card.
        """
        logger.info(f"Locating flight card for flight number: '{flight_number}'")
        cards = self.page.locator(self.FLIGHT_ROW_CARDS)
        total = cards.count()
        target_tokens = [tok.strip() for tok in flight_number.split("-") if len(tok.strip()) > 2]

        for i in range(total):
            card = cards.nth(i)
            num_text = self.get_flight_number(card)
            if flight_number in num_text or num_text in flight_number:
                logger.info(f"Matched flight card #{i} for '{flight_number}'")
                return card
            if any(tok in num_text for tok in target_tokens):
                logger.info(f"Matched flight card #{i} for token from '{flight_number}' (text: '{num_text}')")
                return card

        logger.warning(f"Could not locate flight card '{flight_number}' specifically; returning first card.")
        return cards.first

    def get_flight_number(self, flight_card) -> str:
        """Extracts the Arrival / Departure flight number from a flight card."""
        try:
            flight_num_loc = flight_card.locator(self.ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER).first
            if flight_num_loc.count() > 0 and flight_num_loc.is_visible():
                return flight_num_loc.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    def get_alert_count(self, flight_card) -> str:
        """Extracts the numeric alert count string displayed on the flight card."""
        try:
            # First check the exact number element (<p class='alerts-list'>)
            count_loc = flight_card.locator(self.ALERT_COUNT_ELEMENT).first
            if count_loc.count() > 0 and count_loc.is_visible():
                val = count_loc.inner_text().strip()
                if val:
                    return val

            # Fallback to the alert button wrapper
            btn = flight_card.locator(self.ALERT_COL_BUTTON).first
            if btn.count() > 0 and btn.is_visible():
                val = btn.inner_text().strip()
                if val:
                    return val
        except Exception:
            pass
        return "00"

    def parse_alert_count(self, count_str: str) -> int:
        """Parses the integer value of an alert count string, e.g. '00' -> 0, '01' -> 1."""
        try:
            digits = "".join(ch for ch in str(count_str) if ch.isdigit())
            return int(digits) if digits else 0
        except Exception:
            return 0

    # ==================== THREE-DOTS MENU ACTIONS ====================
    @allure.step("Click Three-Dots Menu on flight card")
    def open_three_dots_menu(self, flight_card):
        """Locates and clicks the three-dots (more_vert / Edit Flight) menu icon on the flight card."""
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"Opening Three-Dots menu for flight '{flight_number}'")
        try:
            flight_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)

            three_dots = flight_card.locator(self.THREE_DOTS_MENU_ICON).first
            expect(three_dots).to_be_visible(timeout=10000)
            three_dots.click()
            logger.info(f"Clicked Three-Dots menu icon on flight '{flight_number}'")

            menu_panel = self.page.locator(self.MENU_PANEL)
            expect(menu_panel).to_be_visible(timeout=5000)
            logger.info("Menu panel is visible")

        except Exception as e:
            self.attach_screenshot(f"three_dots_click_failed_{flight_number}")
            logger.error(f"Failed to open Three-Dots menu for flight '{flight_number}': {e}")
            raise

    # ==================== ADD ALERT / TASK DIALOG ACTIONS ====================
    @allure.step("Select 'Add Alert/Task' from menu")
    def open_add_alert_dialog(self, flight_card):
        """Opens the Three-Dots menu and clicks 'Add Alert/Task' option."""
        self.open_three_dots_menu(flight_card)
        logger.info("Selecting 'Add Alert/Task' from menu")
        try:
            add_alert_opt = self.page.locator(self.ADD_ALERT_TASK_MENU_ITEM).first
            expect(add_alert_opt).to_be_visible(timeout=5000)
            add_alert_opt.click()
            logger.info("Clicked 'Add Alert/Task' menu option")

            task_input = self.page.locator(self.TASK_NAME_INPUT).first
            expect(task_input).to_be_visible(timeout=10000)
            logger.info("Add Alert/Task dialog is visible")

        except Exception as e:
            self.attach_screenshot("open_add_alert_dialog_failed")
            logger.error(f"Failed to open Add Alert/Task dialog: {e}")
            raise

    @allure.step("Fill Alert Form: Category='{category}', Task Name='{task_name}', Type='{alert_type}'")
    def fill_alert_form(
        self,
        category: str = "Alert",
        task_name: str | None = None,
        alert_type: str = "Departure"
    ) -> str:
        """
        Fills the Add Alert/Task popup:
        - If Category is 'Alert' -> Task Name = 'Test Alert'
        - If Category is 'Incident' -> Task Name = 'Test Incident'
        - If Category is 'Task' -> Task Name = 'Test Task'
        - Sets Alert Type to Departure toggle.
        Returns the resolved task_name.
        """
        # Resolve task name based on user rules if not explicitly supplied
        if not task_name:
            cat_lower = category.lower()
            if "alert" in cat_lower:
                task_name = "Test Alert"
            elif "incident" in cat_lower:
                task_name = "Test Incident"
            elif "task" in cat_lower:
                task_name = "Test Task"
            else:
                task_name = f"Test {category}"

        logger.info(
            f"Filling Alert form -> Category: '{category}', Task Name: '{task_name}', Alert Type: '{alert_type}'"
        )
        try:
            # 1. Fill Task Name
            name_input = self.page.locator(self.TASK_NAME_INPUT).first
            expect(name_input).to_be_visible(timeout=5000)
            name_input.fill(task_name)
            logger.info(f"Entered Task Name: '{task_name}'")
            self.page.wait_for_timeout(300)

            # 2. Select Alert Category from PrimeNG dropdown
            category_dd = self.page.locator(self.ALERT_CATEGORY_DROPDOWN).first
            expect(category_dd).to_be_visible(timeout=5000)
            category_dd.click()
            self.page.wait_for_timeout(800)

            # Find matching option in dropdown list
            cat_lower = category.lower()
            if "alert" in cat_lower:
                opt = self.page.locator(self.CATEGORY_OPTION_ALERT).first
            elif "incident" in cat_lower:
                opt = self.page.locator(self.CATEGORY_OPTION_INCIDENT).first
            elif "task" in cat_lower:
                opt = self.page.locator(self.CATEGORY_OPTION_TASK).first
            else:
                opt = self.page.locator(
                    f"//div[contains(@class,'p-dropdown-items-wrapper')]//li[contains(.,'{category}')]"
                ).first

            expect(opt).to_be_visible(timeout=5000)
            opt.click()
            logger.info(f"Selected Alert Category: '{category}'")
            self.page.wait_for_timeout(500)

            # 3. Select Alert Type (Departure toggle by default)
            if alert_type.lower() == "arrival":
                toggle = self.page.locator(self.ALERT_TYPE_ARRIVAL).first
            else:
                toggle = self.page.locator(self.ALERT_TYPE_DEPARTURE).first

            expect(toggle).to_be_visible(timeout=5000)
            toggle.click()
            logger.info(f"Selected Alert Type Toggle: '{alert_type}'")
            self.page.wait_for_timeout(500)

            self.attach_screenshot(f"Alert_Form_Filled_{task_name}")
            return task_name

        except Exception as e:
            self.attach_screenshot("fill_alert_form_failed")
            logger.error(f"Failed to fill Alert form: {e}")
            raise

    @allure.step("Click 'Save' button in Add Alert/Task dialog")
    def click_save_alert(self):
        """Clicks the Save button in the Add Alert/Task popup."""
        logger.info("Clicking Save button in Add Alert/Task dialog")
        try:
            save_btn = self.page.locator(self.ADD_ALERT_SAVE_BUTTON).first
            expect(save_btn).to_be_visible(timeout=5000)
            save_btn.click()
            logger.info("Clicked Save button")

            # Wait for dialog to dismiss
            self.page.wait_for_timeout(2000)

        except Exception as e:
            self.attach_screenshot("save_alert_click_failed")
            logger.error(f"Failed to click Save button: {e}")
            raise

    @allure.step("Create Alert on Flight: Category='{category}'")
    def create_flight_alert(
        self,
        flight_card,
        category: str = "Alert",
        task_name: str | None = None,
        alert_type: str = "Departure"
    ) -> dict:
        """
        Executes end-to-end Alert/Task creation on a flight card:
        1. Opens Three-Dots menu and clicks 'Add Alert/Task'.
        2. Fills Task Name, Alert Category, and Departure toggle.
        3. Clicks Save button.
        Returns dictionary with flight_number, category, task_name, and alert_type.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"--- Starting Alert Creation for Flight: '{flight_number}' ---")

        with allure.step(f"Create Alert for Flight: {flight_number}"):
            self.open_add_alert_dialog(flight_card)
            resolved_task_name = self.fill_alert_form(
                category=category,
                task_name=task_name,
                alert_type=alert_type
            )
            self.click_save_alert()

            # Verify whether fallback success message is displayed after clicking Save
            is_success, msg_text = self.is_success_message_displayed(timeout_sec=7)

            logger.info(
                f"--- Alert creation submitted for '{flight_number}' (Task Name: '{resolved_task_name}', Success Message: '{msg_text}') ---"
            )
            return {
                "flight_number": flight_number,
                "category": category,
                "task_name": resolved_task_name,
                "alert_type": alert_type,
                "is_success": is_success,
                "success_message": msg_text,
            }

    @allure.step("Verify Fallback Success Message after Alert creation")
    def is_success_message_displayed(self, expected_keyword: str = "successfully", timeout_sec: int = 7) -> tuple[bool, str]:
        """
        Verifies whether the system fallback message (e.g., 'Alert raised successfully')
        is displayed in the system after clicking Save.
        Returns:
            (is_displayed: bool, message_text: str)
        """
        logger.info(f"Checking for fallback success message containing '{expected_keyword}'...")
        start_time = time.time()
        while (time.time() - start_time) < timeout_sec:
            snack = self.page.locator(self.SUCCESS_SNACKBAR).first
            if snack.count() > 0 and snack.is_visible():
                text = snack.inner_text().strip()
                logger.info(f"Fallback message detected: '{text}'")
                if expected_keyword.lower() in text.lower() or "success" in text.lower():
                    logger.info(f"SUCCESS: Fallback message verified: '{text}'!")
                    self.attach_screenshot("Alert_Creation_Fallback_Success_Message")
                    return True, text

            self.page.wait_for_timeout(200)

        logger.warning(f"Fallback success message not detected within {timeout_sec}s.")
        return False, ""

    # ==================== REFRESH FLIGHTS & VERIFY ALERT ====================
    @allure.step("Click Refresh Flight icon on List View")
    def refresh_flights_list(self):
        """Clicks the Refresh Flight icon (pi-sync) on the List View toolbar and waits for loading to complete."""
        logger.info("Clicking Refresh Flight icon on List View...")
        try:
            # Move mouse away to ensure toolbar is not hovered/obstructed
            self.page.mouse.move(600, 500)
            self.page.wait_for_timeout(500)

            refresh_icon = self.page.locator(self.REFRESH_FLIGHTS_ICON).first
            expect(refresh_icon).to_be_visible(timeout=10000)
            refresh_icon.click()
            logger.info("Clicked Refresh Flight icon on List View")

            # Wait for system loading spinner to appear and finish
            self.page.wait_for_timeout(1000)
            self.wait_for_loading_to_finish(timeout=20000)

            # Wait for flight cards to be visible and stable
            flights = self.page.locator(self.FLIGHT_ROW_CARDS)
            flights.first.wait_for(state="visible", timeout=20000)
            self.page.wait_for_timeout(1500)
            logger.info(f"Flights list refreshed successfully. Total cards: {flights.count()}")

        except Exception as e:
            self.attach_screenshot("refresh_flights_failed")
            logger.error(f"Failed to refresh flights list: {e}")
            raise

    @allure.step("Refresh Ongoing page and verify Alert count for '{flight_number}'")
    def refresh_and_wait_for_alert_count_update(
        self,
        flight_number: str,
        initial_count: str,
        flight_card=None,
        initial_wait_sec: int = 5,
        retry_interval_sec: int = 5,
        max_attempts: int = 4,
    ) -> tuple[bool, str, any]:
        """
        Refreshes the Ongoing page using the List View refresh icon and checks if the alert count is updated:
        1. Waits initial_wait_sec for backend submission to register.
        2. Clicks the Refresh Flight icon and waits for the loading spinner to complete.
        3. Relocates the target flight card by flight number or uses provided locator.
        4. Checks if the alert count has increased.
        5. If not updated yet, waits retry_interval_sec and clicks refresh icon again (up to max_attempts).
        Returns:
            (is_updated: bool, current_count: str, target_flight_card)
        """
        init_num = self.parse_alert_count(initial_count)
        logger.info(
            f"Checking alert count update for flight '{flight_number}' via Refresh icon "
            f"(Initial: '{initial_count}', parsed: {init_num})"
        )

        # Initial wait before refreshing
        self.page.wait_for_timeout(initial_wait_sec * 1000)

        curr_count = initial_count
        curr_num = init_num
        target_card = flight_card if flight_card is not None else self.get_flight_card_by_number(flight_number)

        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"Refreshing Ongoing flights list (Attempt {attempt}/{max_attempts})..."
            )
            self.refresh_flights_list()

            # Relocate target flight card after system refresh
            target_card = self.get_flight_card_by_number(flight_number)
            curr_count = self.get_alert_count(target_card)
            curr_num = self.parse_alert_count(curr_count)
            logger.info(
                f"After refresh attempt {attempt} -> Flight '{flight_number}' Alert count: '{curr_count}' (parsed: {curr_num})"
            )

            if curr_num > init_num:
                logger.info(
                    f"SUCCESS: Alert count increased from '{initial_count}' to '{curr_count}'!"
                )
                self.attach_screenshot(f"Alert_Count_Updated_After_Refresh_{flight_number}_{curr_count}")
                return True, curr_count, target_card

            if curr_count != initial_count and curr_count != "00":
                logger.info(
                    f"SUCCESS: Alert count changed from '{initial_count}' to '{curr_count}'!"
                )
                self.attach_screenshot(f"Alert_Count_Updated_After_Refresh_{flight_number}_{curr_count}")
                return True, curr_count, target_card

            if attempt < max_attempts:
                logger.info(
                    f"Count not yet increased ('{curr_count}' <= '{initial_count}'). "
                    f"Waiting {retry_interval_sec}s before next refresh..."
                )
                self.page.wait_for_timeout(retry_interval_sec * 1000)

        logger.warning(
            f"Alert count for '{flight_number}' did not increase after {max_attempts} refreshes. Final count: '{curr_count}'"
        )
        self.attach_screenshot(f"Alert_Count_Not_Updated_After_Refresh_{flight_number}_{curr_count}")
        return False, curr_count, target_card

    # ==================== RELOAD & WAIT FOR ALERT COUNT UPDATE ====================
    @allure.step("Reload page and refresh Ongoing section")
    def reload_and_refresh_ongoing_view(self):
        """Reloads the current page, waits for DOM and spinners, and ensures Ongoing section is active."""
        logger.info("Reloading page to refresh flight data...")
        try:
            self.page.reload(wait_until="domcontentloaded")
            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(2000)

            # Check if list view cards are visible; if not, navigate via menu
            cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            if cards.count() == 0 or not cards.first.is_visible():
                logger.info("Flight cards not visible after reload; navigating to Flights List View...")
                self.navigate_to_list_view_page()

            self.ensure_ongoing_section()
            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(1000)
            logger.info("Page reloaded and Ongoing section refreshed successfully.")

        except Exception as e:
            self.attach_screenshot("reload_ongoing_view_failed")
            logger.error(f"Failed to reload and refresh Ongoing view: {e}")
            raise

    @allure.step("Verify Alert count updated for '{flight_number}', reloading if needed")
    def wait_for_alert_count_update_with_reload(
        self,
        flight_number: str,
        initial_count: str,
        initial_wait_sec: int = 5,
        reload_wait_sec: int = 6,
        max_attempts: int = 4,
    ) -> tuple[bool, str, any]:
        """
        Verifies whether the flight alert count is updated without passively waiting for notifications:
        1. Checks the alert count on the card after initial_wait_sec.
        2. If not updated, reloads the page, ensures Ongoing section, relocates the card, and checks again.
        3. Repeats for up to max_attempts.
        Returns:
            (is_updated: bool, current_count: str, updated_flight_card_locator)
        """
        init_num = self.parse_alert_count(initial_count)
        logger.info(
            f"Checking alert count update for flight '{flight_number}' (Initial: '{initial_count}', parsed: {init_num})"
        )

        # Step A: Initial check before reloading
        self.page.wait_for_timeout(initial_wait_sec * 1000)
        target_card = self.get_flight_card_by_number(flight_number)
        curr_count = self.get_alert_count(target_card)
        curr_num = self.parse_alert_count(curr_count)
        logger.info(f"Check before reload -> Alert count: '{curr_count}' (parsed: {curr_num})")

        if curr_num > init_num or (curr_count != initial_count and curr_count != "00"):
            logger.info(f"Alert count already increased to '{curr_count}' without page reload!")
            self.attach_screenshot(f"Alert_Count_Updated_NoReload_{flight_number}_{curr_count}")
            return True, curr_count, target_card

        # Step B: If not updated, reload page once (and retry up to max_attempts if still processing)
        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"Alert count not yet updated ('{curr_count}' <= '{initial_count}'). "
                f"Waiting {reload_wait_sec}s then reloading page (Attempt {attempt}/{max_attempts})..."
            )
            self.page.wait_for_timeout(reload_wait_sec * 1000)
            self.reload_and_refresh_ongoing_view()

            # Relocate flight card after page reload
            target_card = self.get_flight_card_by_number(flight_number)
            curr_count = self.get_alert_count(target_card)
            curr_num = self.parse_alert_count(curr_count)
            logger.info(
                f"Post-reload attempt {attempt} -> Alert count for '{flight_number}': '{curr_count}' (parsed: {curr_num})"
            )

            if curr_num > init_num or (curr_count != initial_count and curr_count != "00"):
                logger.info(
                    f"SUCCESS: Alert count increased to '{curr_count}' after reload attempt {attempt}!"
                )
                self.attach_screenshot(f"Alert_Count_Updated_After_Reload_{flight_number}_{curr_count}")
                return True, curr_count, target_card

        logger.warning(
            f"Alert count for '{flight_number}' did not increase after {max_attempts} reloads. Last count: '{curr_count}'"
        )
        self.attach_screenshot(f"Alert_Count_Not_Updated_{flight_number}_{curr_count}")
        return False, curr_count, target_card

    # ==================== WAIT FOR ALERT COUNT UPDATE ====================
    @allure.step("Wait for Alert count update on flight card (up to {timeout_sec}s)")
    def wait_for_alert_count_update(
        self,
        flight_card,
        initial_count: str,
        timeout_sec: int = 120
    ) -> str:
        """
        Polls the alert count button on the flight card for up to timeout_sec
        (between 30 seconds and 2 minutes) until the count updates.
        Returns the updated count string.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(
            f"Waiting for Alert count on flight '{flight_number}' to update from initial: '{initial_count}' (timeout={timeout_sec}s)"
        )

        start_time = time.time()
        curr_count = initial_count

        while (time.time() - start_time) < timeout_sec:
            self.page.wait_for_timeout(2000)
            elapsed = int(time.time() - start_time)
            curr_count = self.get_alert_count(flight_card)

            if curr_count != initial_count:
                logger.info(
                    f"Alert count updated to '{curr_count}' (was '{initial_count}') after {elapsed}s"
                )
                return curr_count

            if elapsed % 10 == 0:
                logger.info(f"Waiting for alert notification... elapsed: {elapsed}s / {timeout_sec}s")

        logger.warning(
            f"Alert count did not change within {timeout_sec}s. Current count: '{curr_count}'"
        )
        return curr_count

    # ==================== RIGHT-SIDE ALERT POPUP VERIFICATION ====================
    @allure.step("Click Alert Count Number to open right-side Alert Details popup")
    def open_alert_details_popup(self, flight_card):
        """Clicks the Alert count number element on the flight card to open the right-side notification popup."""
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"Clicking Alert Count number for flight '{flight_number}'")
        try:
            num_elem = flight_card.locator(self.ALERT_COUNT_ELEMENT).first
            if not (num_elem.count() > 0 and num_elem.is_visible()):
                num_elem = flight_card.locator(self.ALERT_COL_BUTTON).first

            expect(num_elem).to_be_visible(timeout=10000)
            num_elem.scroll_into_view_if_needed()
            num_elem.click()
            logger.info("Clicked Alert Count number element")

            # Wait for right-side notification popup to be attached/visible
            popup = self.page.locator(self.ALERT_DETAILS_POPUP).first
            expect(popup).to_be_attached(timeout=15000)
            self.page.wait_for_timeout(1500)
            logger.info("Right-side Alert Details popup opened successfully")

            self.attach_screenshot(f"Alert_Details_Popup_{flight_number}")

        except Exception as e:
            self.attach_screenshot("open_alert_details_popup_failed")
            logger.error(f"Failed to open right-side Alert Details popup: {e}")
            raise

    @allure.step("Check whether alert '{expected_task_name}' is displayed in right popup")
    def is_alert_displayed_in_popup(self, expected_task_name: str, timeout_sec: int = 30) -> bool:
        """
        Verifies whether the created alert (by Task Name) is displayed in the
        right-side Alert Details popup list.
        Polls up to timeout_sec for the alert card to appear in the list.
        """
        logger.info(f"Checking if Alert '{expected_task_name}' is displayed in right popup...")
        start_time = time.time()

        while (time.time() - start_time) < timeout_sec:
            popup = self.page.locator(self.ALERT_DETAILS_POPUP).first
            if popup.count() > 0:
                popup_text = popup.inner_text()
                if expected_task_name.lower() in popup_text.lower():
                    logger.info(
                        f"SUCCESS: Alert '{expected_task_name}' found in right-side popup text!"
                    )
                    self.attach_screenshot(f"Alert_Verified_In_Popup_{expected_task_name}")
                    return True

                # Also inspect individual alert cards
                alert_cards = self.page.locator(self.ALERT_CARDS_IN_POPUP)
                card_count = alert_cards.count()
                for i in range(card_count):
                    card_text = alert_cards.nth(i).inner_text()
                    if expected_task_name.lower() in card_text.lower():
                        logger.info(
                            f"SUCCESS: Alert '{expected_task_name}' found in alert card #{i}!"
                        )
                        self.attach_screenshot(f"Alert_Card_Match_{expected_task_name}")
                        return True

            self.page.wait_for_timeout(1000)

        logger.warning(
            f"Alert '{expected_task_name}' was NOT found in right popup within {timeout_sec}s."
        )
        self.attach_screenshot(f"Alert_Not_Found_{expected_task_name}")
        return False

    @allure.step("Close right-side Alert Details popup")
    def close_alert_details_popup(self):
        """Closes the right-side Alert Details popup via its close icon."""
        try:
            close_btn = self.page.locator(self.ALERT_POPUP_CLOSE_BUTTON).first
            if close_btn.is_visible(timeout=3000):
                close_btn.click()
                logger.info("Closed right-side Alert Details popup")
                self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.debug(f"Close alert details popup notice: {e}")


