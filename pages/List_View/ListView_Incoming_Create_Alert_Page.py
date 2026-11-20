# Author : Tilak Badsheshi
# Created Date : 2026-11-18
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-18

"""
==============  INTRODUCTION ================
Page Object / Component: ListView_Incoming_Create_Alert_Page
Description: Page Object Model for Flights List View - Creating flight-level Alert/Task functionality
             in the Incoming section, refreshing the grid via the sync icon, and verifying alert
             presentation in the right-side details popup.

Scenario & Workflow Capabilities:
1. Navigation: Route to Flights List View dashboard via navigation menu.
2. Section Assertion: Ensure Incoming section is active and flights are visible.
3. Alert Creation Workflow:
   - Click Ellipsis menu ('more_vert') on the flight card.
   - Select 'Add Alert/Task' menu option.
   - Enter Task Name ('Test Alert'), select Category ('Alert') from PrimeNG dropdown, select Alert Type ('Arrival').
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


class ListView_Incoming_Create_Alert_Page(BasePage):
    """
    Page Object for Flights List View - Creating Flight-Level Alert/Task functionality
    specifically within the Incoming section, and verifying alert presentation in the
    right-side details popup.
    """

    # ==================== NAVIGATION & TOOLBAR LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    FLIGHTS = "//div[@role='button']/span[text()='Flights'] | //span[normalize-space()='Flights']"
    INCOMING_TAB = "text=Incoming"
    REFRESH_FLIGHTS_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"

    # ==================== FLIGHT CARD LOCATORS ====================
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"
    FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = (
        "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
        "//div[contains(@class,'flightno-col')] | "
        "p[mattooltip='Flight Arrival Departure Numbers']"
    )

    # ==================== ELLIPSIS MENU (ACTIONS COLUMN) ====================
    ELLIPSIS_MENU_ICON = "mat-icon:has-text('more_vert'), mat-icon[mattooltip='Edit Flight']"
    THREE_DOTS_MENU_ICON = ELLIPSIS_MENU_ICON  # Backwards compatibility

    # Menu items inside mat-menu-content
    MENU_PANEL = "//div[contains(@class,'mat-menu-content')]"
    ADD_ALERT_TASK_MENU_ITEM = (
        "//div[contains(@class,'mat-menu-content')]//button[contains(.,'Add Alert/Task')] | "
        "//div[contains(@class,'mat-menu-content')]//span[normalize-space()='Add Alert/Task'] | "
        "//button[@role='menuitem'][contains(.,'Add Alert/Task')]"
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
    ALERT_COUNT_ELEMENT = (
        "p.alerts-list, p[class*='alerts_p'], .alerts-col p, "
        "p[class*='Incoming_alerts_p'], p[class*='Ongoing_alerts_p']"
    )
    ALERT_COL_BUTTON = (
        "button.Incoming_alerts_button_Two, button.Ongoing_alerts_button_Two, "
        "button[class*='alerts_button'], .alerts-col button, p.alerts-list"
    )
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

    # Loading Spinners
    SPINNER_SELECTORS = [
        ".loading",
        ".spinner",
        ".mat-progress-spinner",
    ]

    # ==================== CONSTRUCTOR ====================
    def __init__(self, page: Page, base_url: str | None = None):
        """
        Initializes the Incoming Flights Create Alert page object.

        What this function does:
        Sets up the web page controller and prepares all tools needed to interact with the
        Flights List View screen and its Incoming tab.

        Why we use it:
        This is the starting point whenever a test needs to interact with incoming flights
        and create new alerts.
        """
        super().__init__(page, base_url)
        self.page = page

    # ==================== SCREENSHOT ====================
    def attach_screenshot(self, name: str, full_page: bool = True):
        """
        Captures a picture of the current browser screen and attaches it to the test report.

        What this function does:
        Takes an image of what is currently displayed on the screen and attaches it directly
        to the Allure test report.

        Why we use it:
        This allows non-technical managers and testers to visually see what happened at each
        step of the test, and provides clear visual proof if any step fails.

        Inputs:
            name (str): A simple name describing what is shown in the image (for example, 'incoming_alert_form_filled').
            full_page (bool): Set to True to capture the entire web page from top to bottom.
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
        Checks if any loading circles or spinners are active on the screen. If they are, it
        pauses and waits patiently until the system finishes loading before continuing.

        Why we use it:
        Prevents test actions from failing while the application is still fetching flight
        data from the server.

        Inputs:
            timeout (int): Maximum time in milliseconds to wait for spinners to disappear (defaults to 15 seconds).
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
        Opens the main navigation menu on the top-left and clicks on the 'Flights' option
        so that the user is brought directly to the Flights List View table.

        Step-by-step actions:
        1. Checks if the page is currently on the login screen. If so, clicks Submit to finish logging in.
        2. Hovers the mouse over the top-left hamburger menu icon to open the navigation drawer.
        3. Clicks on the 'Flights' menu option.
        4. Moves the mouse away towards the center of the screen so the navigation drawer closes smoothly.
        5. Waits for any loading spinners to complete.
        6. Confirms that flight cards are visible on the screen.
        """
        logger.info("Navigating to Flights List View")
        try:
            # Check if still on the login screen and submit if needed
            if "login" in self.page.url:
                logger.info("Currently on login page; ensuring login submission completes...")
                login_btn = self.page.locator("//button[@type='submit']").first
                if login_btn.is_visible():
                    login_btn.click()
                self.page.wait_for_timeout(3000)

            # Locate and hover over the top-left navigation menu icon
            menu = self.page.locator(self.MENU).first
            expect(menu).to_be_visible(timeout=30000)
            menu.hover()
            self.page.wait_for_timeout(1000)

            # Locate the Flights option in the opened menu
            flights = self.page.locator(self.FLIGHTS).first
            if not flights.is_visible():
                logger.warning("Flights option not visible after hover, clicking Menu")
                menu.click()
                self.page.wait_for_timeout(1000)

            expect(flights).to_be_visible(timeout=15000)
            flights.click()
            logger.info("Clicked Flights in navigation menu")

            # Move the mouse away to allow the navigation drawer to close
            self.page.mouse.move(600, 500)
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(2000)

            # Confirm that the flight cards have loaded on the screen
            flights_card = self.page.locator(self.FLIGHT_ROW_CARDS)
            expect(flights_card.first).to_be_visible(timeout=30000)
            logger.info("Flights List View loaded successfully")

        except Exception as e:
            self.attach_screenshot("list_view_navigation_failed")
            logger.error(f"Failed to navigate to Flights List View: {e}")
            raise

    # ==================== SECTION HANDLING ====================
    @allure.step("Ensure Incoming Section is selected")
    def ensure_incoming_section(self) -> int:
        """
        Switches to the 'Incoming' flights section and verifies flight cards are loaded.

        What this function does:
        Clicks on the 'Incoming' tab at the top of the Flights List View screen to display
        all arriving flights. It then counts how many incoming flight cards are currently
        visible on the screen.

        Step-by-step actions:
        1. Moves the mouse to the center of the screen to close any open dropdowns or menus.
        2. Finds and clicks the 'Incoming' tab button.
        3. Waits for the page loading spinner to finish.
        4. If flight cards do not appear right away, clicks the Refresh Flight icon to reload them.
        5. Checks if there is a 'No Flights Available' message. If so, returns 0.
        6. Counts and returns the total number of incoming flight cards displayed.

        Returns:
            int: The total count of incoming flight cards currently visible on the screen.
        """
        logger.info("Ensuring Incoming section tab is active")
        try:
            # Move mouse to neutral area so menus close
            self.page.mouse.move(600, 500)
            self.page.wait_for_timeout(500)

            # Locate and click the 'Incoming' section tab
            incoming_tab = self.page.locator(self.INCOMING_TAB).first
            if incoming_tab.count() == 0 or not incoming_tab.is_visible():
                incoming_tab = self.page.locator(
                    "//div[contains(.,'Incoming') and not(contains(@class,'card'))] | "
                    "//span[contains(text(),'Incoming')]"
                ).first

            expect(incoming_tab).to_be_visible(timeout=15000)
            incoming_tab.scroll_into_view_if_needed()
            incoming_tab.click()
            logger.info("Clicked Incoming section tab")

            self.page.wait_for_timeout(2000)
            self.wait_for_loading_to_finish()

            # Ensure flight cards appear; if not immediately loaded, try clicking the refresh icon
            card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
            try:
                card_loc.first.wait_for(state="visible", timeout=8000)
            except Exception:
                sync_icon = self.page.locator(self.REFRESH_FLIGHTS_ICON).first
                if sync_icon.count() > 0 and sync_icon.is_visible():
                    sync_icon.click()
                    self.page.wait_for_timeout(3500)

            # Check if there are zero flights available in this section
            no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE).first
            if no_flights.count() > 0 and no_flights.is_visible():
                logger.info("Incoming section currently has 0 flights available.")
                return 0

            count = card_loc.count()
            logger.info(f"Incoming section active. Total flight cards: {count}")
            return count

        except Exception as e:
            self.attach_screenshot("incoming_section_activation_failed")
            logger.error(f"Failed to activate Incoming section: {e}")
            raise

    # ==================== FLIGHT CARD HELPERS ====================
    def get_flight_card_with_actions_menu(self):
        """
        Finds the first flight card that has an active actions (ellipsis) menu.

        What this function does:
        Scans through all incoming flight cards on the screen from top to bottom. It returns
        the first flight card that has an enabled three-dot menu button.

        Why we use it:
        Some flights might be locked or may not allow new alerts. This function guarantees
        that we pick a valid, editable flight card to create our alert on.

        Returns:
            Locator: The web element representing the eligible flight card.
        """
        flights = self.page.locator(self.FLIGHT_ROW_CARDS)
        total = flights.count()
        logger.info(f"Searching for an unlocked flight card with actions menu among {total} cards...")
        for i in range(total):
            card = flights.nth(i)
            ellipsis_btn = card.locator(self.ELLIPSIS_MENU_ICON).first
            if ellipsis_btn.count() > 0 and ellipsis_btn.is_visible():
                flight_num = self.get_flight_number(card)
                logger.info(f"Selected flight card #{i} ('{flight_num}') with available ellipsis menu")
                return card

        logger.warning("No flight card found with explicitly visible ellipsis menu; falling back to first card.")
        return flights.first

    def get_flight_card_by_number(self, flight_number: str):
        """
        Finds a specific flight card on the screen using its flight number.

        What this function does:
        Looks through all visible flight cards and matches the one that has the requested
        flight number (for example, 'FZ-0215').

        Inputs:
            flight_number (str): The flight number text to search for.

        Returns:
            Locator: The matching flight card web element.
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
        """
        Reads and returns the flight number from a flight card.

        What this function does:
        Inspects the flight card element and extracts the text displaying the flight's
        arrival and departure numbers (for example, 'FZ-0215').

        Inputs:
            flight_card: The flight card web element to read from.

        Returns:
            str: The flight number text, or 'Unknown Flight' if not found.
        """
        try:
            num = super().get_flight_number(flight_card)
            if num and num != "Unknown Flight":
                return num
            flight_num_loc = flight_card.locator(self.ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER).first
            if flight_num_loc.count() > 0 and flight_num_loc.is_visible():
                return flight_num_loc.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    def get_alert_count(self, flight_card) -> str:
        """
        Reads the current alert count number displayed on a flight card.

        What this function does:
        Finds the alert counter badge or button on the flight card and reads its number
        (for example, '00', '01', or '02').

        Inputs:
            flight_card: The flight card web element to inspect.

        Returns:
            str: The alert count text as displayed on the screen (defaults to '00').
        """
        try:
            count_loc = flight_card.locator(self.ALERT_COUNT_ELEMENT).first
            if count_loc.count() > 0 and count_loc.is_visible():
                val = count_loc.inner_text().strip()
                if val:
                    return val

            btn = flight_card.locator(self.ALERT_COL_BUTTON).first
            if btn.count() > 0 and btn.is_visible():
                val = btn.inner_text().strip()
                if val:
                    return val
        except Exception:
            pass
        return "00"

    def parse_alert_count(self, count_str: str) -> int:
        """
        Converts an alert count text into a regular whole number (integer).

        What this function does:
        Takes an alert count string like '01' or '02' and extracts its digits to return
        a normal number like 1 or 2. This allows tests to compare whether the number increased.

        Inputs:
            count_str (str): The text representation of the number (e.g., '01').

        Returns:
            int: The numeric value (e.g., 1).
        """
        try:
            digits = "".join(ch for ch in str(count_str) if ch.isdigit())
            return int(digits) if digits else 0
        except Exception:
            return 0

    # ==================== ELLIPSIS MENU ACTIONS ====================
    @allure.step("Click Ellipsis Menu on flight card")
    def open_ellipsis_menu(self, flight_card):
        """
        Clicks the three-dot ellipsis menu button on a flight card.

        What this function does:
        Locates the three vertical dots (ellipsis menu icon) on the right side of a flight
        card and clicks it to open the actions menu popup.

        Step-by-step actions:
        1. Scrolls the flight card into view so it is clearly visible on the screen.
        2. Clicks the three-dot ellipsis menu button.
        3. Waits for the menu dropdown list to appear.

        Inputs:
            flight_card: The flight card whose menu we want to open.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"Opening ellipsis menu for flight '{flight_number}'")
        try:
            # Scroll card into view
            flight_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)

            # Click the ellipsis menu icon on the flight card
            ellipsis_btn = flight_card.locator(self.ELLIPSIS_MENU_ICON).first
            expect(ellipsis_btn).to_be_visible(timeout=10000)
            ellipsis_btn.click()
            logger.info(f"Clicked ellipsis menu icon on flight '{flight_number}'")

            # Verify that the menu panel popped up
            menu_panel = self.page.locator(self.MENU_PANEL)
            expect(menu_panel).to_be_visible(timeout=5000)
            logger.info("Menu panel is visible")

        except Exception as e:
            self.attach_screenshot(f"ellipsis_menu_click_failed_{flight_number}")
            logger.error(f"Failed to open ellipsis menu for flight '{flight_number}': {e}")
            raise

    # Backwards compatibility alias
    open_three_dots_menu = open_ellipsis_menu

    # ==================== ADD ALERT / TASK DIALOG ACTIONS ====================
    @allure.step("Select 'Add Alert/Task' from menu")
    def open_add_alert_dialog(self, flight_card):
        """
        Opens the ellipsis menu and selects the 'Add Alert/Task' option.

        What this function does:
        Clicks the three-dot menu on the flight card, then clicks the 'Add Alert/Task'
        menu option to open the alert creation popup form.

        Step-by-step actions:
        1. Clicks the ellipsis menu button on the flight card.
        2. Locates and clicks the 'Add Alert/Task' item in the menu dropdown.
        3. Waits for the alert popup window and its task name text box to appear on screen.

        Inputs:
            flight_card: The flight card element we want to create an alert for.
        """
        self.open_ellipsis_menu(flight_card)
        logger.info("Selecting 'Add Alert/Task' from menu")
        try:
            # Click 'Add Alert/Task' in the menu dropdown
            add_alert_opt = self.page.locator(self.ADD_ALERT_TASK_MENU_ITEM).first
            expect(add_alert_opt).to_be_visible(timeout=5000)
            add_alert_opt.click()
            logger.info("Clicked 'Add Alert/Task' menu option")

            # Verify that the dialog's task name input field is visible
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
        alert_type: str = "Arrival"
    ) -> tuple[str, str]:
        """
        Fills out the alert creation form with all required details.

        What this function does:
        Enters the alert name, selects the category from the dropdown menu, and selects
        the appropriate alert type (Arrival, Departure, or Turnaround).

        Business Rules & Behavior:
        1. Task Name:
           - If Category is 'Alert', the name defaults to 'Test Alert'.
           - If Category is 'Incident', the name defaults to 'Test Incident'.
           - If Category is 'Task', the name defaults to 'Test Task'.
        2. Alert Category:
           - Opens the category dropdown and selects the matching option (e.g., 'Alert').
        3. Alert Type Toggle:
           - If the Departure/Arrival toggle button is present on the screen, it clicks Departure or Arrival.
           - If the toggle button is not present, this flight is a turnaround flight, so 'Turnaround' is selected.

        Inputs:
            category (str): The category of the alert ('Alert', 'Task', or 'Incident').
            task_name (str | None): Optional custom name. If not provided, it is chosen automatically based on category.
            alert_type (str): The desired alert type (defaults to 'Arrival').

        Returns:
            tuple[str, str]: A pair containing (the resolved task name, the resolved alert type).
        """
        # Determine default task name if not explicitly provided
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
            # 1. Type the Task Name into the input box
            name_input = self.page.locator(self.TASK_NAME_INPUT).first
            expect(name_input).to_be_visible(timeout=5000)
            name_input.fill(task_name)
            logger.info(f"Entered Task Name: '{task_name}'")
            self.page.wait_for_timeout(300)

            # 2. Open the Alert Category dropdown list
            category_dd = self.page.locator(self.ALERT_CATEGORY_DROPDOWN).first
            expect(category_dd).to_be_visible(timeout=5000)
            category_dd.click()
            self.page.wait_for_timeout(800)

            # Locate and click the desired category option in the dropdown list
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

            # 3. Handle Alert Type:
            # If the toggle buttons exist, click the appropriate direction (Departure or Arrival).
            # If no toggle button is present, the flight is a turnaround flight.
            resolved_alert_type = "Turnaround"
            departure_toggle = self.page.locator(self.ALERT_TYPE_DEPARTURE).first
            arrival_toggle = self.page.locator(self.ALERT_TYPE_ARRIVAL).first

            if departure_toggle.count() > 0 and departure_toggle.is_visible():
                logger.info("Alert Type Departure toggle is present. Selecting 'Departure'...")
                departure_toggle.click()
                resolved_alert_type = "Departure"
                self.page.wait_for_timeout(400)
            elif arrival_toggle.count() > 0 and arrival_toggle.is_visible():
                logger.info("Departure toggle not visible, but Arrival toggle is visible. Selecting Arrival...")
                arrival_toggle.click()
                resolved_alert_type = "Arrival"
                self.page.wait_for_timeout(400)
            else:
                logger.info("Alert Type toggle is NOT present -> Flight is a Turnaround flight ('Turnaround' displayed).")
                resolved_alert_type = "Turnaround"

            self.attach_screenshot(f"Incoming_Alert_Form_Filled_{task_name}")
            return task_name, resolved_alert_type

        except Exception as e:
            self.attach_screenshot("fill_alert_form_failed")
            logger.error(f"Failed to fill Alert form: {e}")
            raise

    @allure.step("Click 'Save' button in Add Alert/Task dialog")
    def click_save_alert(self):
        """
        Clicks the Save button in the alert form to submit the new alert.

        What this function does:
        Finds the 'Save' button at the bottom of the Add Alert dialog and clicks it.
        It then pauses briefly to let the application process the submission.
        """
        logger.info("Clicking Save button in Add Alert/Task dialog")
        try:
            save_btn = self.page.locator(self.ADD_ALERT_SAVE_BUTTON).first
            expect(save_btn).to_be_visible(timeout=5000)
            save_btn.click()
            logger.info("Clicked Save button")
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
        alert_type: str = "Arrival"
    ) -> dict:
        """
        Performs the complete alert creation process from start to finish.

        What this function does:
        Orchestrates all actions needed to create an alert for an incoming flight:
        1. Opens the three-dot ellipsis menu on the flight card.
        2. Selects 'Add Alert/Task' to open the form.
        3. Fills in the task name, category, and alert type.
        4. Clicks the 'Save' button.
        5. Checks if a confirmation success message appears on screen.

        Inputs:
            flight_card: The flight card element to attach the alert to.
            category (str): The alert category (defaults to 'Alert').
            task_name (str | None): The name of the alert (defaults to 'Test Alert').
            alert_type (str): The flight direction (e.g., 'Arrival').

        Returns:
            dict: A summary dictionary with flight number, category, task name, alert type,
                  and whether the success message was displayed.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"--- Starting Alert Creation for Incoming Flight: '{flight_number}' ---")

        with allure.step(f"Create Alert for Flight: {flight_number}"):
            # Open the alert form from the flight card's menu
            self.open_add_alert_dialog(flight_card)

            # Fill in the form fields
            resolved_task_name, resolved_alert_type = self.fill_alert_form(
                category=category,
                task_name=task_name,
                alert_type=alert_type
            )

            # Click the Save button
            self.click_save_alert()

            # Check if the green success notification message appeared
            is_success, msg_text = self.is_success_message_displayed(timeout_sec=7)

            logger.info(
                f"--- Alert creation submitted for '{flight_number}' (Task Name: '{resolved_task_name}', Alert Type: '{resolved_alert_type}', Success Message: '{msg_text}') ---"
            )
            return {
                "flight_number": flight_number,
                "category": category,
                "task_name": resolved_task_name,
                "alert_type": resolved_alert_type,
                "is_success": is_success,
                "success_message": msg_text,
            }

    @allure.step("Verify Fallback Success Message after Alert creation")
    def is_success_message_displayed(self, expected_keyword: str = "successfully", timeout_sec: int = 7) -> tuple[bool, str]:
        """
        Checks if a success confirmation banner appears on screen after saving an alert.

        What this function does:
        Monitors the screen for up to a few seconds looking for a notification popup
        (such as 'Alert raised successfully').

        Why we use it:
        This confirms that the application successfully registered the new alert in the backend.

        Inputs:
            expected_keyword (str): A word that should be in the message (e.g., 'successfully').
            timeout_sec (int): Maximum seconds to wait for the message (defaults to 7 seconds).

        Returns:
            tuple[bool, str]: (True if message was found, the actual text of the message).
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
                    self.attach_screenshot("Incoming_Alert_Creation_Fallback_Success_Message")
                    return True, text

            self.page.wait_for_timeout(200)

        logger.warning(f"Fallback success message not detected within {timeout_sec}s.")
        return False, ""

    # ==================== REFRESH FLIGHTS & VERIFY ALERT ====================
    @allure.step("Click Refresh Flight icon on List View")
    def refresh_flights_list(self):
        """
        Clicks the Refresh Flight icon to reload all flight cards on the screen.

        What this function does:
        Locates the circular sync/refresh button in the Flights toolbar and clicks it.
        It then waits for the loading animation to finish and ensures the flight cards are visible.
        """
        logger.info("Clicking Refresh Flight icon on List View...")
        try:
            # Move mouse to neutral area so toolbar is clear
            self.page.mouse.move(600, 500)
            self.page.wait_for_timeout(500)

            # Find and click the Refresh Flight icon
            refresh_icon = self.page.locator(self.REFRESH_FLIGHTS_ICON).first
            expect(refresh_icon).to_be_visible(timeout=10000)
            refresh_icon.click()
            logger.info("Clicked Refresh Flight icon on List View")

            # Wait for the system loading spinner to disappear
            self.page.wait_for_timeout(1000)
            self.wait_for_loading_to_finish(timeout=20000)

            # Confirm that the flight cards are back and visible
            flights = self.page.locator(self.FLIGHT_ROW_CARDS)
            flights.first.wait_for(state="visible", timeout=20000)
            self.page.wait_for_timeout(1500)
            logger.info(f"Flights list refreshed successfully. Total cards: {flights.count()}")

        except Exception as e:
            self.attach_screenshot("refresh_flights_failed")
            logger.error(f"Failed to refresh flights list: {e}")
            raise

    @allure.step("Refresh Incoming page and verify Alert count for '{flight_number}'")
    def refresh_and_wait_for_alert_count_update(
        self,
        flight_number: str,
        initial_count: str,
        flight_card=None,
        initial_wait_sec: int = 4,
        retry_interval_sec: int = 5,
        max_attempts: int = 4,
    ) -> tuple[bool, str, any]:
        """
        Refreshes the flights list and verifies that the flight's alert count has increased.

        What this function does:
        After creating an alert, the flight card's alert counter needs to increase (for example, from '00' to '01').
        This function:
        1. Clicks the Refresh Flight icon.
        2. Waits for the new flight data to load.
        3. Reads the flight's new alert count.
        4. If the number increased, the check passes immediately.
        5. If not updated yet, it waits and retries refreshing up to 4 times.

        Inputs:
            flight_number (str): The flight number being verified.
            initial_count (str): The starting count before creating the alert (e.g., '00').
            flight_card: The flight card element.
            initial_wait_sec (int): Seconds to wait before the very first refresh.
            retry_interval_sec (int): Seconds to wait between refresh attempts.
            max_attempts (int): Maximum number of refresh retries allowed.

        Returns:
            tuple[bool, str, any]: (True if count increased, the updated count text, the updated flight card).
        """
        init_num = self.parse_alert_count(initial_count)
        logger.info(
            f"Checking alert count update for flight '{flight_number}' via Refresh icon "
            f"(Initial: '{initial_count}', parsed: {init_num})"
        )

        # Pause briefly to allow the server to finish saving the alert
        self.page.wait_for_timeout(initial_wait_sec * 1000)

        curr_count = initial_count
        target_card = flight_card if flight_card is not None else self.get_flight_card_by_number(flight_number)

        # Try refreshing up to max_attempts times
        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"Refreshing Incoming flights list (Attempt {attempt}/{max_attempts})..."
            )
            self.refresh_flights_list()

            # Find the flight card again after the refresh
            target_card = self.get_flight_card_by_number(flight_number)
            curr_count = self.get_alert_count(target_card)
            curr_num = self.parse_alert_count(curr_count)
            logger.info(
                f"After refresh attempt {attempt} -> Flight '{flight_number}' Alert count: '{curr_count}' (parsed: {curr_num})"
            )

            # Check if the alert count has increased
            if curr_num > init_num:
                logger.info(
                    f"SUCCESS: Alert count increased from '{initial_count}' to '{curr_count}'!"
                )
                self.attach_screenshot(f"Incoming_Alert_Count_Updated_After_Refresh_{flight_number}_{curr_count}")
                return True, curr_count, target_card

            if curr_count != initial_count and curr_count != "00":
                logger.info(
                    f"SUCCESS: Alert count changed from '{initial_count}' to '{curr_count}'!"
                )
                self.attach_screenshot(f"Incoming_Alert_Count_Updated_After_Refresh_{flight_number}_{curr_count}")
                return True, curr_count, target_card

            # If not yet updated, wait before trying again
            if attempt < max_attempts:
                logger.info(
                    f"Count not yet increased ('{curr_count}' <= '{initial_count}'). "
                    f"Waiting {retry_interval_sec}s before next refresh..."
                )
                self.page.wait_for_timeout(retry_interval_sec * 1000)

        logger.warning(
            f"Alert count for '{flight_number}' did not increase after {max_attempts} refreshes. Final count: '{curr_count}'"
        )
        self.attach_screenshot(f"Incoming_Alert_Count_Not_Updated_After_Refresh_{flight_number}_{curr_count}")
        return False, curr_count, target_card

    # ==================== RIGHT-SIDE ALERT POPUP VERIFICATION ====================
    @allure.step("Click Alert Count Number to open right-side Alert Details popup")
    def open_alert_details_popup(self, flight_card):
        """
        Opens the right-side Alert Details panel by clicking the alert number on the flight card.

        What this function does:
        Clicks on the alert counter number (e.g., '01') on the flight card. This opens a slide-out
        panel on the right side of the screen that lists all alerts created for this flight.

        Inputs:
            flight_card: The flight card whose alert details we want to open.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"Clicking Alert Count number for flight '{flight_number}'")
        try:
            # Find and click the alert count badge/button
            num_elem = flight_card.locator(self.ALERT_COUNT_ELEMENT).first
            if not (num_elem.count() > 0 and num_elem.is_visible()):
                num_elem = flight_card.locator(self.ALERT_COL_BUTTON).first

            expect(num_elem).to_be_visible(timeout=10000)
            num_elem.scroll_into_view_if_needed()
            num_elem.click()
            logger.info("Clicked Alert Count number element")

            # Verify that the right-side popup opened
            popup = self.page.locator(self.ALERT_DETAILS_POPUP).first
            expect(popup).to_be_attached(timeout=15000)
            self.page.wait_for_timeout(1500)
            logger.info("Right-side Alert Details popup opened successfully")

            self.attach_screenshot(f"Incoming_Alert_Details_Popup_{flight_number}")

        except Exception as e:
            self.attach_screenshot("open_alert_details_popup_failed")
            logger.error(f"Failed to open right-side Alert Details popup: {e}")
            raise

    @allure.step("Check whether alert '{expected_task_name}' is displayed in right popup")
    def is_alert_displayed_in_popup(self, expected_task_name: str, timeout_sec: int = 30) -> bool:
        """
        Verifies that our new alert is listed inside the right-side Alert Details panel.

        What this function does:
        Looks inside the open right-side panel and checks whether the name of our alert
        (such as 'Test Alert') is displayed in the list of alert cards.

        Why we use it:
        This confirms that the alert was not just saved in the background, but is visible
        and readable by users who view the flight's alert details.

        Inputs:
            expected_task_name (str): The alert title to check for (e.g., 'Test Alert').
            timeout_sec (int): Maximum seconds to wait for the alert to show up in the panel.

        Returns:
            bool: True if the alert is found in the panel, False otherwise.
        """
        logger.info(f"Checking if Alert '{expected_task_name}' is displayed in right popup...")
        start_time = time.time()

        while (time.time() - start_time) < timeout_sec:
            popup = self.page.locator(self.ALERT_DETAILS_POPUP).first
            if popup.count() > 0:
                # Check overall popup text
                popup_text = popup.inner_text()
                if expected_task_name.lower() in popup_text.lower():
                    logger.info(
                        f"SUCCESS: Alert '{expected_task_name}' found in right-side popup text!"
                    )
                    self.attach_screenshot(f"Incoming_Alert_Verified_In_Popup_{expected_task_name}")
                    return True

                # Check individual alert cards inside the popup
                alert_cards = self.page.locator(self.ALERT_CARDS_IN_POPUP)
                card_count = alert_cards.count()
                for i in range(card_count):
                    card_text = alert_cards.nth(i).inner_text()
                    if expected_task_name.lower() in card_text.lower():
                        logger.info(
                            f"SUCCESS: Alert '{expected_task_name}' found in alert card #{i}!"
                        )
                        self.attach_screenshot(f"Incoming_Alert_Card_Match_{expected_task_name}")
                        return True

            self.page.wait_for_timeout(1000)

        logger.warning(
            f"Alert '{expected_task_name}' was NOT found in right popup within {timeout_sec}s."
        )
        self.attach_screenshot(f"Incoming_Alert_Not_Found_{expected_task_name}")
        return False

    @allure.step("Close right-side Alert Details popup")
    def close_alert_details_popup(self):
        """
        Closes the right-side Alert Details panel.

        What this function does:
        Finds and clicks the 'X' (close) button at the top corner of the right-side alert
        panel so that the screen returns to its normal view.
        """
        try:
            close_btn = self.page.locator(self.ALERT_POPUP_CLOSE_BUTTON).first
            if close_btn.is_visible(timeout=3000):
                close_btn.click()
                logger.info("Closed right-side Alert Details popup")
                self.page.wait_for_timeout(1000)
        except Exception as e:
            logger.debug(f"Close alert details popup notice: {e}")
