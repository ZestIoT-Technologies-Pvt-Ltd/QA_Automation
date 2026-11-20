# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: List_View_Ongoing_Lock_Unlock_Flight_Page
Description: Page Object Model for Flights List View sequential Locking and Unlocking Flight functionality
             (First Lock -> Then Unlock) specifically restricted to the Ongoing section. Handles dialog
             submissions, reason/remarks inputs, and visual lock indicator status checks.

Scenario & Workflow Capabilities:
1. Navigation: Route to Flights List View dashboard via navigation menu.
2. Section Assertion: Ensure Ongoing section is active and load flight cards.
3. Lock Status Detection: Check whether the target flight card is Locked or Unlocked.
4. Flight Locking Workflow (Step 1):
   - Click Ellipsis menu ('more_vert') on an unlocked flight card.
   - Select 'Lock Flight' option from menu.
   - Fill Reason ('Test') and Remarks ('Testing Flight').
   - Submit lock dialog and assert flight card displays lock icon button.
5. Flight Unlocking Workflow (Step 2):
   - Click Lock icon button directly on the locked flight card.
   - Enter Remarks ('Testing Unlock') in the unlock popup.
   - Confirm unlock action and verify flight transitions to unlocked state.
"""

import time
import allure
from playwright.sync_api import Page, expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class List_View_Ongoing_Lock_Unlock_Flight_Page(BasePage):
    """
    Page Object for Flights List View - Locking and Unlocking Flight functionality
    specifically within the Ongoing section.
    """

    # ==================== NAVIGATION LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    FLIGHTS = "//div[@role='button']/span[text()='Flights']"
    ONGOING_TAB = "//div[contains(text(),'Ongoing')]"

    # ==================== FLIGHT CARD LOCATORS ====================
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"
    FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = (
        "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
        "//div[contains(@class,'flightno-col')] | "
        "//p[@mattooltip='Flight Arrival Departure Numbers']"
    )

    # ==================== ELLIPSIS MENU (ACTIONS COLUMN) ====================
    ELLIPSIS_MENU_ICON = "mat-icon:has-text('more_vert'), mat-icon[mattooltip='Edit Flight']"
    THREE_DOTS_MENU_ICON = ELLIPSIS_MENU_ICON  # Backwards compatibility

    # Menu items inside mat-menu-content
    MENU_PANEL = "//div[contains(@class,'mat-menu-content')]"
    LOCK_FLIGHT_MENU_ITEM = (
        "//div[contains(@class,'mat-menu-content')]//button[contains(.,'Lock Flight')] | "
        "//div[contains(@class,'mat-menu-content')]//span[normalize-space()='Lock Flight']"
    )
    UNLOCK_FLIGHT_MENU_ITEM = (
        "//div[contains(@class,'mat-menu-content')]//button[contains(.,'Unlock Flight')] | "
        "//div[contains(@class,'mat-menu-content')]//span[normalize-space()='Unlock Flight']"
    )

    # ==================== LOCK FLIGHT DIALOG ====================
    LOCK_FLIGHT_DIALOG = (
        "//mat-dialog-container[.//h5[contains(text(),'Lock')] or .//*[contains(text(),'Lock flight')]] | "
        "//form[contains(@class,'lock-dialog')] | "
        "//mat-dialog-container"
    )
    LOCK_FLIGHT_REASON_INPUT = "//input[@formcontrolname='lock_reason']"
    LOCK_FLIGHT_REMARKS_INPUT = "//input[@formcontrolname='remarks']"
    LOCK_FLIGHT_SUBMIT_BUTTON = (
        "//mat-dialog-container//button[normalize-space()='Lock'] | "
        "//div[contains(@class,'lock-row')]//button[contains(.,'Lock')] | "
        "//form[contains(@class,'lock-dialog')]//button[@type='submit'] | "
        "//form[contains(@class,'lock-dialog')]//button[contains(@class,'savebutton')]"
    )
    LOCK_FLIGHT_CANCEL_BUTTON = (
        "//mat-dialog-container//button[normalize-space()='Cancel'] | "
        "//form[contains(@class,'lock-dialog')]//button[contains(.,'Cancel')]"
    )
    LOCK_FLIGHT_CLOSE_ICON = "//mat-icon[@mat-dialog-close and normalize-space()='close']"

    # ==================== LOCK ICON BUTTON (ON FLIGHT CARD) ====================
    LOCK_ICON_BUTTON = ".lock-icon, div[class*='lock-icon'], img[src*='lock'], .colorHeader.lock-icon"

    # ==================== UNLOCK FLIGHT DIALOG ====================
    UNLOCK_FLIGHT_DIALOG = (
        "//form[contains(@class,'lock-dialog')] | "
        "//mat-dialog-container[.//h5[contains(text(),'Lock') or contains(text(),'Unlock')]]"
    )
    UNLOCK_REMARKS_INPUT = (
        "//input[@formcontrolname='remarks'] | "
        "//textarea[@formcontrolname='remarks'] | "
        "//input[@placeholder='Remarks'] | "
        "//textarea[@placeholder='Remarks']"
    )
    UNLOCK_SUBMIT_BUTTON = (
        "//mat-dialog-container//button[normalize-space()='Unlock'] | "
        "//form[contains(@class,'lock-dialog')]//button[normalize-space()='Unlock'] | "
        "//form[contains(@class,'lock-dialog')]//button[@type='submit'] | "
        "//button[contains(@class,'savebutton') and (contains(.,'Unlock') or contains(.,'Lock'))] | "
        "//button[@type='submit']"
    )

    # ==================== TOAST MESSAGES ====================
    TOAST_MESSAGE = (
        "//div[contains(@class,'simple-snack-bar')] | "
        "//div[contains(@class,'toast')] | "
        "//div[@role='status']"
    )

    # ==================== LOADING SPINNERS ====================
    SPINNER_SELECTORS = [
        ".loading",
        ".spinner",
        ".mat-progress-spinner",
    ]

    # ==================== CONSTRUCTOR ====================
    def __init__(self, page: Page, base_url: str | None = None):
        """
        Initializes the Ongoing Flights Lock/Unlock page object.

        What this function does:
        Sets up the page controller and prepares everything needed to interact with the
        Flights List View screen and lock/unlock ongoing flights.
        """
        super().__init__(page, base_url)
        self.page = page

    # ==================== SCREENSHOT ====================
    def attach_screenshot(self, name: str, full_page: bool = True):
        """
        Captures a screenshot of the current screen and saves it into the test report.

        What this function does:
        Takes an image of what is visible on the web page and attaches it directly to the
        test report so that managers and testers can visually see what happened.

        Inputs:
            name (str): A descriptive name for the image (e.g., 'Flight_Locked_FZ-0101').
            full_page (bool): True to capture the entire page from top to bottom.
        """
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
        """
        Waits for all loading spinners on the page to disappear.

        What this function does:
        Checks if any loading circles or spinners are active on the screen and pauses
        until the system finishes loading before performing the next action.

        Inputs:
            timeout (int): Maximum time in milliseconds to wait (defaults to 15 seconds).
        """
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
        """
        Navigates from the home dashboard to the Flights List View screen.

        What this function does:
        Opens the main navigation menu and clicks on 'Flights' so that the user is brought
        directly to the Flights List View table.

        Step-by-step actions:
        1. Hovers over the top-left menu icon to reveal menu options.
        2. Clicks on the 'Flights' menu option.
        3. Moves the mouse away so the menu drawer closes smoothly.
        4. Waits for any loading spinners to disappear.
        5. Verifies that flight cards are visible on the screen.
        """
        logger.info("Navigating to Flights List View")
        try:
            menu = self.page.locator(self.MENU)
            expect(menu).to_be_visible(timeout=20000)
            menu.hover()
            self.page.wait_for_timeout(1000)

            flights = self.page.locator(self.FLIGHTS)
            if not flights.is_visible():
                logger.warning("Flights option not visible after hover, clicking Menu")
                menu.click()
                self.page.wait_for_timeout(1000)

            expect(flights).to_be_visible(timeout=15000)
            flights.click()
            logger.info("Clicked Flights in navigation menu")

            self.page.mouse.move(600, 500)
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(2000)

            # Verify list view cards are loaded (with sync retry if needed)
            flights_card = self.page.locator(self.FLIGHT_ROW_CARDS)
            try:
                flights_card.first.wait_for(state="visible", timeout=15000)
            except Exception:
                sync_icon = self.page.locator("//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]").first
                if sync_icon.count() > 0 and sync_icon.is_visible():
                    logger.info("Clicking Refresh Flight icon to trigger flight load...")
                    sync_icon.click()
                    self.wait_for_loading_to_finish()
                    self.page.wait_for_timeout(3000)

            expect(flights_card.first).to_be_visible(timeout=30000)
            logger.info("Flights List View loaded successfully")

        except Exception as e:
            self.attach_screenshot("list_view_navigation_failed")
            logger.error(f"Failed to navigate to Flights List View: {e}")
            raise

    # ==================== SECTION HANDLING ====================
    @allure.step("Ensure Ongoing Section is selected")
    def ensure_ongoing_section(self):
        """
        Switches to the 'Ongoing' flights section and verifies flight cards are loaded.

        What this function does:
        Clicks on the 'Ongoing' tab at the top of the Flights List View screen to display
        all currently active flights. It returns the total count of ongoing flight cards.

        Returns:
            int: The total count of ongoing flight cards currently visible on the screen.
        """
        logger.info("Ensuring Ongoing section tab is active")
        try:
            ongoing_tab = self.page.locator(self.ONGOING_TAB).first
            expect(ongoing_tab).to_be_visible(timeout=15000)
            ongoing_tab.click()
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
    def get_flight_number(self, flight_card) -> str:
        """
        Reads and returns the flight number from a flight card.

        What this function does:
        Inspects the flight card element and extracts the flight number text
        (for example, 'FZ-0215').

        Inputs:
            flight_card: The flight card web element to read from.

        Returns:
            str: The flight number text, or 'Unknown Flight' if not found.
        """
        try:
            num = super().get_flight_number(flight_card)
            if num and num != "Unknown Flight":
                return num
            flight_num_loc = flight_card.locator(self.ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER)
            if flight_num_loc.count() > 0 and flight_num_loc.first.is_visible():
                return flight_num_loc.first.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    @allure.step("Check whether flight is locked")
    def is_flight_locked(self, flight_card) -> bool:
        """
        Checks whether a flight card is currently locked.

        What this function does:
        Looks at the flight card on screen to see if a red/prominent lock icon button is present.
        If the lock icon button is displayed, the flight is locked.
        If the lock icon button is absent, the flight is unlocked.

        Inputs:
            flight_card: The flight card element to check.

        Returns:
            bool: True if the flight is locked, False if it is unlocked.
        """
        flight_number = self.get_flight_number(flight_card)
        try:
            flight_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(300)
            lock_elem = flight_card.locator(self.LOCK_ICON_BUTTON).first
            if lock_elem.count() > 0 and lock_elem.is_visible():
                logger.info(f"Flight '{flight_number}' is LOCKED (lock icon button is displayed)")
                return True
            else:
                logger.info(f"Flight '{flight_number}' is NOT LOCKED (lock icon button is absent)")
                return False
        except Exception as e:
            logger.warning(f"Error checking locked status for '{flight_number}': {e}")
            return False

    def wait_for_lock_state(self, flight_card, expected_locked: bool = True, timeout_ms: int = 12000) -> bool:
        """
        Waits until the flight card reaches the expected locked or unlocked state.

        What this function does:
        Checks the flight card every second until its lock status matches what we expect
        (for example, waiting for it to become locked, or waiting for it to become unlocked).

        Inputs:
            flight_card: The flight card element.
            expected_locked (bool): True if waiting to become locked, False if waiting to become unlocked.
            timeout_ms (int): Maximum time in milliseconds to wait.

        Returns:
            bool: True if the expected state was reached, False if it timed out.
        """
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            if self.is_flight_locked(flight_card) == expected_locked:
                return True
            self.page.wait_for_timeout(1000)
        return self.is_flight_locked(flight_card) == expected_locked

    # ==================== ELLIPSIS MENU ACTIONS ====================
    @allure.step("Click Ellipsis Menu on flight card")
    def open_ellipsis_menu(self, flight_card):
        """
        Clicks the three-dot ellipsis menu button on a flight card.

        What this function does:
        Locates the three vertical dots (ellipsis menu icon) on the right side of a flight
        card and clicks it to open the actions menu dropdown.

        Step-by-step actions:
        1. Scrolls the flight card into view.
        2. Clicks the three-dot ellipsis menu button.
        3. Waits for the menu popup panel to appear.

        Inputs:
            flight_card: The flight card whose menu we want to open.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"Opening ellipsis menu for flight '{flight_number}'")
        try:
            flight_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)

            ellipsis_btn = flight_card.locator(self.ELLIPSIS_MENU_ICON).first
            expect(ellipsis_btn).to_be_visible(timeout=10000)
            ellipsis_btn.click()
            logger.info(f"Clicked ellipsis menu icon on flight '{flight_number}'")

            # Wait for menu content overlay
            menu_panel = self.page.locator(self.MENU_PANEL)
            expect(menu_panel).to_be_visible(timeout=5000)
            logger.info("Menu panel is visible")

        except Exception as e:
            self.attach_screenshot(f"ellipsis_menu_click_failed_{flight_number}")
            logger.error(f"Failed to open ellipsis menu for flight '{flight_number}': {e}")
            raise

    # Backwards compatibility alias
    open_three_dots_menu = open_ellipsis_menu

    # ==================== LOCK FLIGHT ACTIONS ====================
    @allure.step("Select 'Lock Flight' from menu")
    def click_lock_flight_option(self):
        """
        Clicks the 'Lock Flight' option from the opened ellipsis dropdown menu.

        What this function does:
        Selects 'Lock Flight' in the actions menu, opening the Lock Flight dialog popup.
        """
        logger.info("Selecting 'Lock Flight' option from menu")
        try:
            lock_opt = self.page.locator(self.LOCK_FLIGHT_MENU_ITEM).first
            expect(lock_opt).to_be_visible(timeout=5000)
            lock_opt.click()
            logger.info("Clicked 'Lock Flight' menu option")

            # Verify Lock Flight dialog appears
            dialog = self.page.locator(self.LOCK_FLIGHT_DIALOG).first
            expect(dialog).to_be_visible(timeout=10000)
            logger.info("Lock Flight dialog opened successfully")

        except Exception as e:
            self.attach_screenshot("click_lock_flight_option_failed")
            logger.error(f"Failed to select 'Lock Flight' option: {e}")
            raise

    @allure.step("Enter Reason: '{reason}' and Remarks: '{remarks}' in Lock Flight dialog")
    def fill_lock_details(self, reason: str = "Test", remarks: str = "Testing Flight"):
        """
        Enters the Reason and Remarks in the Lock Flight popup dialog.

        What this function does:
        Fills the 'Reason' input box (e.g. 'Test') and the 'Remarks' input box
        (e.g. 'Testing Flight') before submitting the lock.

        Inputs:
            reason (str): The reason for locking the flight.
            remarks (str): Additional notes or remarks.
        """
        logger.info(f"Filling Lock details -> Reason: '{reason}', Remarks: '{remarks}'")
        try:
            # 1. Fill Reason
            reason_input = self.page.locator(self.LOCK_FLIGHT_REASON_INPUT).first
            expect(reason_input).to_be_visible(timeout=5000)
            reason_input.fill(reason)
            logger.info(f"Entered Reason: '{reason}'")

            # 2. Fill Remarks
            remarks_input = self.page.locator(self.LOCK_FLIGHT_REMARKS_INPUT).first
            expect(remarks_input).to_be_visible(timeout=5000)
            remarks_input.fill(remarks)
            logger.info(f"Entered Remarks: '{remarks}'")

            self.page.wait_for_timeout(500)

        except Exception as e:
            self.attach_screenshot("fill_lock_details_failed")
            logger.error(f"Failed to enter Reason and Remarks in Lock dialog: {e}")
            raise

    @allure.step("Click 'Lock' button in Lock Flight dialog")
    def click_lock_button(self):
        """
        Clicks the 'Lock' button inside the popup dialog to confirm locking the flight.

        What this function does:
        Finds and clicks the primary 'Lock' submission button and waits for the dialog to close.
        """
        logger.info("Clicking 'Lock' button in dialog")
        try:
            lock_btn = self.page.locator(self.LOCK_FLIGHT_SUBMIT_BUTTON).first
            expect(lock_btn).to_be_visible(timeout=5000)
            expect(lock_btn).to_be_enabled(timeout=5000)
            btn_html = lock_btn.evaluate("el => el.outerHTML")
            logger.info(f"Target Lock button HTML: {btn_html}")
            lock_btn.click()
            logger.info("Clicked 'Lock' button successfully")

            # Wait for dialog to close
            self.page.wait_for_timeout(1500)
            dialog = self.page.locator(self.LOCK_FLIGHT_DIALOG).first
            try:
                dialog.wait_for(state="detached", timeout=8000)
                logger.info("Lock Flight dialog closed successfully (detached)")
            except Exception:
                if dialog.is_visible():
                    logger.warning("Dialog still visible after first click. Re-attempting click with force=True...")
                    lock_btn.click(force=True)
                    self.page.wait_for_timeout(2000)
                    if dialog.is_visible():
                        expect(dialog).not_to_be_visible(timeout=5000)
            logger.info("Lock Flight dialog closed successfully")

        except Exception as e:
            self.attach_screenshot("click_lock_button_failed")
            logger.error(f"Failed to click 'Lock' button: {e}")
            raise

    # ==================== END-TO-END LOCK FLIGHT METHOD ====================
    @allure.step("Lock flight: '{reason}' / '{remarks}'")
    def lock_flight(
        self,
        flight_card,
        reason: str = "Test",
        remarks: str = "Testing Flight"
    ) -> dict:
        """
        Locks a currently unlocked flight card from start to finish.

        What this function does:
        1. Reads the flight number from the card.
        2. Clicks the ellipsis (three-dot) menu on the card.
        3. Clicks 'Lock Flight' from the menu.
        4. Enters the lock Reason (e.g., 'Test') and Remarks (e.g., 'Testing Flight').
        5. Clicks the 'Lock' confirmation button.
        6. Waits for the lock icon button to appear on the flight card.
        7. Takes a screenshot as evidence.

        Inputs:
            flight_card: The flight card element to lock.
            reason (str): Reason for locking.
            remarks (str): Additional notes.

        Returns:
            dict: Summary with flight number, reason, remarks, and whether the flight is locked.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"--- Starting Lock Flight Process for: {flight_number} ---")

        with allure.step(f"Locking Flight: {flight_number}"):
            # 1. Open ellipsis menu
            self.open_ellipsis_menu(flight_card)

            # 2. Click Lock Flight option
            self.click_lock_flight_option()

            # 3. Fill Reason and Remarks
            self.fill_lock_details(reason=reason, remarks=remarks)
            self.attach_screenshot(f"Lock_Dialog_Filled_{flight_number}")

            # 4. Click Lock button
            self.click_lock_button()

            # 5. Wait for lock icon button to appear on flight card
            self.wait_for_lock_state(flight_card, expected_locked=True, timeout_ms=12000)
            self.attach_screenshot(f"Flight_Locked_{flight_number}")

            is_locked = self.is_flight_locked(flight_card)
            logger.info(
                f"--- Lock Flight Process completed for: {flight_number} (is_locked={is_locked}) ---"
            )

            return {
                "flight_number": flight_number,
                "reason": reason,
                "remarks": remarks,
                "is_locked": is_locked,
            }

    # ==================== UNLOCK FLIGHT ACTIONS ====================
    @allure.step("Unlock flight with Remarks: '{remarks}'")
    def unlock_flight(self, flight_card, remarks: str = "Testing Unlock") -> dict:
        """
        Unlocks a currently locked flight card from start to finish.

        What this function does:
        1. Reads the flight number from the card.
        2. Clicks the lock icon button displayed on the flight card to open the unlock popup.
        3. Enters the unlock remarks (e.g., 'Testing Unlock').
        4. Clicks the 'Unlock' confirmation button.
        5. Waits for the lock icon button to disappear from the card.
        6. Takes a screenshot confirming the flight is now unlocked.

        Inputs:
            flight_card: The locked flight card element to unlock.
            remarks (str): Unlock remarks text.

        Returns:
            dict: Summary with flight number, remarks, and whether the flight is locked (should be False).
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"--- Starting Unlock Flight Process for: {flight_number} ---")

        with allure.step(f"Unlocking Flight: {flight_number}"):
            # 1. Click on the lock icon button displayed on the flight card
            lock_elem = flight_card.locator(self.LOCK_ICON_BUTTON).first
            expect(lock_elem).to_be_visible(timeout=10000)
            lock_elem.scroll_into_view_if_needed()
            lock_elem.click()
            logger.info(f"Clicked lock icon button on flight card '{flight_number}'")
            self.page.wait_for_timeout(1000)

            # 2. Enter Remarks in the popup dialog
            remarks_input = self.page.locator(self.UNLOCK_REMARKS_INPUT).first
            if remarks_input.is_visible(timeout=5000):
                remarks_input.fill(remarks)
                logger.info(f"Entered Remarks: '{remarks}' in unlock dialog")

            # Check if reason input is present/required
            reason_input = self.page.locator(self.LOCK_FLIGHT_REASON_INPUT).first
            if reason_input.is_visible(timeout=2000):
                reason_input.fill("Testing Unlock")

            self.page.wait_for_timeout(500)
            self.attach_screenshot(f"Unlock_Dialog_Filled_{flight_number}")

            # 3. Click the Unlock submit button
            unlock_btn = self.page.locator(self.UNLOCK_SUBMIT_BUTTON).first
            expect(unlock_btn).to_be_visible(timeout=5000)
            expect(unlock_btn).to_be_enabled(timeout=5000)
            btn_html = unlock_btn.evaluate("el => el.outerHTML")
            logger.info(f"Target Unlock button HTML: {btn_html}")
            unlock_btn.click()
            logger.info("Clicked Unlock submit button in dialog")

            # Wait for dialog to close
            self.page.wait_for_timeout(1500)
            dialog = self.page.locator(self.UNLOCK_FLIGHT_DIALOG).first
            try:
                dialog.wait_for(state="detached", timeout=8000)
                logger.info("Unlock Flight dialog closed successfully (detached)")
            except Exception:
                if dialog.is_visible():
                    logger.warning("Unlock dialog still visible after first click. Re-attempting click with force=True...")
                    unlock_btn.click(force=True)
                    self.page.wait_for_timeout(2000)
                    if dialog.is_visible():
                        expect(dialog).not_to_be_visible(timeout=5000)
            logger.info("Unlock Flight dialog closed successfully")

            # 4. Wait for flight to be unlocked (lock icon button disappears)
            self.wait_for_lock_state(flight_card, expected_locked=False, timeout_ms=12000)
            self.attach_screenshot(f"Flight_Unlocked_{flight_number}")

            is_locked = self.is_flight_locked(flight_card)
            logger.info(
                f"--- Completed Unlock Flight Process for: {flight_number} (is_locked={is_locked}) ---"
            )
            return {
                "flight_number": flight_number,
                "remarks": remarks,
                "is_locked": is_locked,
            }


# Alias to support both class naming conventions
ListView_Ongoing_Lock_Unlock_Flight_Page = List_View_Ongoing_Lock_Unlock_Flight_Page

