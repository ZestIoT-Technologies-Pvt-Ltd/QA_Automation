# Author : Tilak Badsheshi
# Created Date : 2026-11-09
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: Listview_OngoingSection_Flag_Unflag_Flight
Description: Page Object Model for Flights List View sequential Flagging (Bookmark) and Unflagging
             functionality (First Flag -> Then Unflag) across Ongoing and Incoming flight sections.

Scenario & Workflow Capabilities:
1. Navigation: Route to Flights List View dashboard via navigation menu.
2. Section Iteration: Process flights restricted strictly to Ongoing and Incoming sections.
3. Flag Detection: Check whether the target flight card is currently Flagged or Unflagged.
4. Flagging Workflow (Step 1):
   - Click the Bookmark icon button on an unflagged flight card.
   - Select flag reason from PrimeNG/Material dropdown (e.g. 'Priority Flight').
   - Submit flag configuration and verify the card enters the Flagged state.
5. Unflagging Workflow (Step 2):
   - Click the active Bookmark icon button on the flagged flight card.
   - Click the 'Unflag' confirmation button in the dialog.
   - Verify the card transitions to the Unflagged state.
"""

import time
import pytest
import allure
from playwright.sync_api import Page, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class Listview_OngoingSection_Flag_Unflag_Flight(BasePage):
    """
    Page Object for Flights List View Flagging (Bookmark) functionality
    across Ongoing and Incoming sections.
    """

    # ==================== NAVIGATION LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    FLIGHTS = "//div[@role='button']/span[text()='Flights']"

    # ==================== SECTION TABS (ONGOING & INCOMING ONLY) ====================
    SECTIONS = [
        {"name": "Ongoing", "tab": "//div[contains(text(),'Ongoing')]"},
        {"name": "Incoming", "tab": "//div[contains(text(),'Incoming')]"}
    ]

    # ==================== FLIGHT CARD LOCATORS ====================
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = "//p[@mattooltip='Flight Arrival Departure Numbers']"

    # ==================== BOOKMARK / FLAGGING LOCATORS ====================
    # Bookmark icon button on each flight card
    BOOKMARK_ICON_BUTTON = "//div[contains(@class,'flag-col')]//button"

    # Flagging popup / dialog container
    FLAG_POPUP = "//div[contains(@class,'flag-config')]"

    # Flag reason dropdown trigger inside popup or menu
    FLAG_REASON_DROPDOWN = (
        "//mat-select[@placeholder='Flag Reason'] | "
        "//mat-select[contains(@placeholder,'Flag')] | "
        "//mat-dialog-container//mat-select"
    )

    # Available flag options in dropdown / listbox
    FLAG_DROPDOWN_OPTIONS = (
        "//div[@role='listbox']//mat-option | "
        "//div[contains(@class,'mat-select-panel')]//mat-option"
    )
    FLAG_DROPDOWN_OPTION_BY_TEXT = "//div[@role='listbox']//mat-option/span[text() = 'Priority Flight']"

    # Flag submit / save button
    FLAG_SUBMIT_BUTTON = (
        "//mat-dialog-container//button[normalize-space()='Flag'] | "
        "//div[contains(@class,'flag-config')]//button[normalize-space()='Flag'] | "
        "//button[normalize-space()='Flag'] | "
        "//div[contains(@class,'flag-config')]//button[contains(@class,'savebutton')]"
    )
    FLAG_UNFLAG_SUBMIT_BUTTON = FLAG_SUBMIT_BUTTON
    UNFLAG_BUTTON = (
        "//mat-dialog-container//button[normalize-space()='Unflag'] | "
        "//div[contains(@class,'flag-config')]//button[normalize-space()='Unflag'] | "
        "//button[normalize-space()='Unflag'] | "
        "//div[contains(@class,'flag-config')]//button[contains(.,'Unflag')] | "
        "//mat-dialog-container//button[contains(.,'Unflag')] | "
        "//button[contains(@class,'savebutton') and contains(.,'Unflag')]"
    )

    # Definitive attribute for Flagged state:
    # If flight is FLAGGED -> mattooltip="UnMark Flight" is PRESENT
    # If flight is NOT FLAGGED -> mattooltip="UnMark Flight" is ABSENT
    # Scoped with .// for relative XPath and CSS for direct child matching
    FLAGGED_FLIGHT_ELEMENT = ".//*[@mattooltip='UnMark Flight' or @ng-reflect-message='UnMark Flight']"
    FLAGGED_FLIGHT_CSS = "[mattooltip='UnMark Flight'], [ng-reflect-message='UnMark Flight']"

    # Unflag / Remove Flag button inside popup / dialog
    FLAGGED_ICON = (
        "//div[contains(@class,'flag-col')]//mat-icon[normalize-space()='bookmark'] | "
        "//mat-icon[normalize-space()='bookmark' and not(normalize-space()='bookmark_border')] | "
        "//button[contains(@class,'flagged') or contains(@class,'active')] | "
        "//div[contains(@class,'flag-col') and (contains(@class,'flagged') or contains(@class,'active'))]"
    )

    UNFLAGGED_ICON = (
        "//div[contains(@class,'flag-col')]//mat-icon[normalize-space()='bookmark_border'] | "
        "//mat-icon[normalize-space()='bookmark_border']"
    )

    # Close button for flag popup
    FLAG_POPUP_CLOSE_BUTTON = (
        "//div[contains(@class,'flag-config')]//mat-icon[text()='close'] | "
        "//button[contains(@class,'close')]"
    )

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

    # ==================== SCREENSHOT ====================
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

            # Verify list view cards are present (with sync retry if needed)
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
    @allure.step("Switch to {section_name} Section")
    def switch_to_section(self, section_name: str, tab_locator: str):
        """Switches to the specified section tab (Ongoing or Incoming)."""
        logger.info(f"Switching to {section_name} section tab")
        try:
            tab = self.page.locator(tab_locator).first
            expect(tab).to_be_visible(timeout=15000)
            tab.click()
            logger.info(f"Clicked {section_name} section tab")

            self.wait_for_loading_to_finish()
            self.page.wait_for_timeout(2000)

        except Exception as e:
            self.attach_screenshot(f"{section_name}_tab_switch_failed")
            logger.error(f"Failed to switch to {section_name} tab: {e}")
            raise

    def flights_are_visible(self, section_name: str = "") -> bool:
        """Checks if flight cards are visible in the current section."""
        with allure.step(f"Check if flights are visible in {section_name}"):
            self.page.wait_for_timeout(2000)
            no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)
            if no_flights.count() > 0 and no_flights.first.is_visible():
                logger.warning(f"No flights available in {section_name} section.")
                return False

            flights = self.page.locator(self.FLIGHT_ROW_CARDS)
            try:
                expect(flights.first).to_be_visible(timeout=15000)
                count = flights.count()
                logger.info(f"Flights are visible in {section_name}. Count = {count}")
                return True
            except Exception as e:
                logger.warning(f"No flights loaded in {section_name}: {e}")
                return False

    def count_of_flights(self) -> int:
        """Returns the total number of flight cards loaded in current view."""
        flights = self.page.locator(self.FLIGHT_ROW_CARDS)
        count = flights.count()
        logger.info(f"Total flights found: {count}")
        return count

    def get_flight_number(self, flight_card) -> str:
        """Extracts the Arrival / Departure flight number from a flight card."""
        try:
            flight_num_loc = flight_card.locator(self.ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER)
            if flight_num_loc.count() > 0 and flight_num_loc.first.is_visible():
                return flight_num_loc.first.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    # ==================== FLAGGING (BOOKMARK) ACTIONS ====================
    @allure.step("Click Bookmark (Flag) icon on flight card")
    def click_bookmark_icon(self, flight_card) -> bool:
        """Locates and clicks the bookmark (flag) icon on a given flight card."""
        try:
            flight_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)

            bookmark = flight_card.locator(self.BOOKMARK_ICON_BUTTON).first
            expect(bookmark).to_be_visible(timeout=10000)
            bookmark.scroll_into_view_if_needed()
            bookmark.click()
            logger.info("Clicked Bookmark (Flag) icon on flight card")
            self.page.wait_for_timeout(1000)
            return True
        except Exception as e:
            self.attach_screenshot("bookmark_click_failed")
            logger.error(f"Failed to click Bookmark icon: {e}")
            raise

    @allure.step("Open Flag Reason dropdown")
    def open_flag_dropdown(self):
        """Clicks the Flag Reason dropdown inside the popup if not already expanded."""
        try:
            options_loc = self.page.locator(self.FLAG_DROPDOWN_OPTIONS)
            if options_loc.count() > 0 and options_loc.first.is_visible():
                return

            dropdown = self.page.locator(self.FLAG_REASON_DROPDOWN).first
            if dropdown.is_visible(timeout=5000):
                dropdown.scroll_into_view_if_needed()
                dropdown.click()
                logger.info("Clicked Flag Reason dropdown trigger")
                self.page.wait_for_timeout(1000)

                # Retry click if options listbox did not open
                if not self.page.locator(self.FLAG_DROPDOWN_OPTIONS).first.is_visible():
                    logger.warning("Options listbox not visible after first click; clicking mat-select-trigger...")
                    trigger = dropdown.locator(".mat-select-trigger, .mat-select-arrow-wrapper, .mat-select-value").first
                    if trigger.is_visible():
                        trigger.click()
                    else:
                        dropdown.click(force=True)
                    self.page.wait_for_timeout(1000)
            else:
                logger.info("Flag options may already be open as a direct menu")
        except Exception as e:
            logger.warning(f"Flag Reason dropdown click notice: {e}")

    @allure.step("Fetch available Flagging options")
    def get_available_flag_options(self) -> list[str]:
        """Retrieves and logs all available flag options from the dropdown."""
        try:
            options_loc = self.page.locator(self.FLAG_DROPDOWN_OPTIONS)
            if not options_loc.first.is_visible():
                self.open_flag_dropdown()

            expect(options_loc.first).to_be_visible(timeout=10000)

            count = options_loc.count()
            options = []
            for i in range(count):
                opt_text = options_loc.nth(i).inner_text().strip()
                if opt_text:
                    options.append(opt_text)

            logger.info(f"Available Flagging options ({len(options)}): {options}")
            return options
        except Exception as e:
            self.attach_screenshot("fetch_flag_options_failed")
            logger.error(f"Failed to fetch flag options: {e}")
            raise

    @allure.step("Select Flag option by text value: '{flag_name}'")
    def select_flag_option(self, flag_name: str | None = None) -> str:
        """
        Selects one flag from the dropdown options based strictly on the text value
        present in that dropdown options (not by series / index).
        """
        try:
            available_options = self.get_available_flag_options()
            if not available_options:
                raise ValueError("No flag options available in dropdown to select")

            # Determine the exact text value to select
            selected_text = flag_name.strip() if flag_name else available_options[0]

            # If flag_name was provided, find the matching option text
            if flag_name:
                matched_text = next((opt for opt in available_options if flag_name.lower() in opt.lower()), None)
                if matched_text:
                    selected_text = matched_text
                else:
                    logger.warning(
                        f"Requested flag '{flag_name}' not found in {available_options}. "
                        f"Defaulting to available text: '{selected_text}'"
                    )

            logger.info(f"Selecting flag option by text value: '{selected_text}'")

            # Locate option strictly by its text value in the dropdown options
            option_by_text = self.page.locator(
                f"//div[@role='listbox']//mat-option[.//span[normalize-space()='{selected_text}'] or normalize-space()='{selected_text}']"
            ).first

            # Fallback to text filter if needed
            if not option_by_text.is_visible():
                option_by_text = self.page.locator("//div[@role='listbox']//mat-option").filter(has_text=selected_text).first

            expect(option_by_text).to_be_visible(timeout=10000)
            option_by_text.scroll_into_view_if_needed()
            option_by_text.click()
            logger.info(f"Successfully clicked flag option with text value: '{selected_text}'")
            self.page.wait_for_timeout(1000)
            return selected_text

        except Exception as e:
            self.attach_screenshot("select_flag_by_text_failed")
            logger.error(f"Failed to select flag option by text value: {e}")
            raise

    @allure.step("Save / Submit Flagging")
    def submit_flag(self):
        """Clicks the Flag / Submit button to apply the selected flag."""
        try:
            # Ensure dropdown listbox is closed before clicking Flag button
            listbox = self.page.locator("//div[@role='listbox'] | //div[contains(@class,'mat-select-panel')]").first
            try:
                listbox.wait_for(state="hidden", timeout=3000)
            except Exception:
                pass

            submit_btn = self.page.locator(self.FLAG_SUBMIT_BUTTON).first
            expect(submit_btn).to_be_visible(timeout=5000)
            expect(submit_btn).to_be_enabled(timeout=5000)
            submit_btn.click()
            logger.info("Clicked 'Flag' submit button")
            self.page.wait_for_timeout(1000)

            # Wait for dialog to close
            dialog = self.page.locator("//mat-dialog-container | //div[contains(@class,'flag-config')]").first
            try:
                dialog.wait_for(state="detached", timeout=8000)
                logger.info("Flag Details dialog closed successfully (detached)")
            except Exception:
                if dialog.is_visible():
                    logger.warning("Dialog still visible after first submit click. Re-attempting click with force=True...")
                    submit_btn.click(force=True)
                    self.page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Submit flag button notice: {e}")

    # ==================== END-TO-END FLAGGING METHOD ====================
    def flag_flight(self, flight_card, flag_name: str | None = None) -> dict:
        """
        Executes end-to-end flight flagging for a flight card:
        1. Identifies flight number
        2. Clicks Bookmark icon
        3. Opens Flag dropdown
        4. Fetches and logs available flag options
        5. Selects one flag option
        6. Submits / saves the flag
        7. Attaches Allure screenshot
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"--- Starting Flagging Process for Flight: {flight_number} ---")

        with allure.step(f"Flagging Flight: {flight_number}"):
            # 1. Click Bookmark (Flag) icon
            self.click_bookmark_icon(flight_card)

            # 2. Open dropdown if needed
            self.open_flag_dropdown()

            # 3. Read available options
            available_flags = self.get_available_flag_options()

            # 4. Select one flag
            selected_flag = self.select_flag_option(flag_name)

            # 5. Submit / Save
            self.submit_flag()

            # Wait for flight card to reflect flagged state in DOM
            try:
                flight_card.locator(self.FLAGGED_FLIGHT_CSS).wait_for(state="visible", timeout=10000)
                logger.info(f"mattooltip='UnMark Flight' appeared for flight '{flight_number}'")
            except Exception:
                self.page.wait_for_timeout(3000)

            # 6. Capture screenshot of completion
            self.attach_screenshot(f"Flagged_{flight_number}_{selected_flag}")

            logger.info(f"--- Completed Flagging for Flight: {flight_number} with Flag: '{selected_flag}' ---")
            return {
                "flight_number": flight_number,
                "selected_flag": selected_flag,
                "available_flags": available_flags,
            }

    # ==================== FLAGGED STATE VALIDATION ====================
    @allure.step("Check whether flight is flagged")
    def is_flight_flagged(self, flight_card) -> bool:
        """
        Determines whether the given flight card is currently flagged.
        Identified via the presence of mattooltip='UnMark Flight':
        - If mattooltip='UnMark Flight' is PRESENT -> Flight is FLAGGED.
        - If mattooltip='UnMark Flight' is ABSENT -> Flight is NOT FLAGGED.
        """
        flight_number = self.get_flight_number(flight_card)
        try:
            flight_card.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)

            # Scoped check for mattooltip="UnMark Flight" specifically within this flight card
            unmark_elem = flight_card.locator(self.FLAGGED_FLIGHT_CSS)
            has_unmark = unmark_elem.count() > 0

            # Also check if flight card has flag data badge and IconOne
            has_flag_data = flight_card.locator(".Ongoing_flag_data").count() > 0
            has_icon_one = flight_card.locator(".Ongoing_flag_IconOne").count() > 0

            if has_unmark or (has_flag_data and has_icon_one):
                logger.info(
                    f"Flight '{flight_number}' is FLAGGED (attribute mattooltip='UnMark Flight' is PRESENT)"
                )
                return True
            else:
                logger.info(
                    f"Flight '{flight_number}' is NOT FLAGGED (attribute mattooltip='UnMark Flight' is ABSENT)"
                )
                return False

        except Exception as e:
            logger.warning(f"Error checking if flight '{flight_number}' is flagged: {e}")
            return False

    def wait_for_flag_state(self, flight_card, expected_flagged: bool = True, timeout_ms: int = 12000) -> bool:
        """
        Polls up to timeout_ms until the flight card reaches the expected flagged state.
        If state not reached, triggers a refresh flight sync to reload state from server.
        """
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            if self.is_flight_flagged(flight_card) == expected_flagged:
                return True
            self.page.wait_for_timeout(1000)

        # Retry after clicking refresh flight icon if state didn't update via websocket
        try:
            sync_icon = self.page.locator("//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]").first
            if sync_icon.count() > 0 and sync_icon.is_visible():
                logger.info("Triggering Refresh Flight sync to verify updated flag state...")
                sync_icon.click()
                self.wait_for_loading_to_finish()
                self.page.wait_for_timeout(2000)
                flight_card = self.page.locator(self.FLIGHT_ROW_CARDS).first
        except Exception:
            pass

        return self.is_flight_flagged(flight_card) == expected_flagged

    # ==================== UNFLAGGING ACTIONS ====================
    @allure.step("Unflag flight")
    def unflag_flight(self, flight_card) -> bool:
        """
        Unflags a flagged flight:
        1. Checks whether the flight is currently flagged (has mattooltip='UnMark Flight').
        2. Clicks the Bookmark / UnMark Flight icon on the flight card.
        3. Clicks the 'Unflag' button in the Flag Details popup.
        4. Waits for mattooltip='UnMark Flight' to disappear from the flight card.
        5. Validates that mattooltip='UnMark Flight' is no longer present.
        6. Attaches Allure screenshot.
        """
        flight_number = self.get_flight_number(flight_card)
        logger.info(f"--- Starting Unflagging Process for Flight: {flight_number} ---")

        with allure.step(f"Unflagging Flight: {flight_number}"):
            # 1. Verify before unflagging
            if not self.is_flight_flagged(flight_card):
                logger.warning(
                    f"Flight '{flight_number}' is already UNFLAGGED (mattooltip='UnMark Flight' absent)."
                )
                return True

            logger.info(
                f"Confirmed: Flight '{flight_number}' is FLAGGED (mattooltip='UnMark Flight' present). "
                f"Proceeding with unflag action."
            )

            # 2. Click the Bookmark / UnMark Flight icon on the flagged flight card
            unmark_icon = flight_card.locator(self.FLAGGED_FLIGHT_CSS).first
            if unmark_icon.is_visible():
                unmark_icon.scroll_into_view_if_needed()
                unmark_icon.click()
                logger.info(f"Clicked element with mattooltip='UnMark Flight' on flight '{flight_number}'")
            else:
                self.click_bookmark_icon(flight_card)

            self.page.wait_for_timeout(1500)

            # 3. Locate and click the 'Unflag' button in the Flag Details dialog
            unflag_btn = self.page.locator(self.UNFLAG_BUTTON).first
            if unflag_btn.is_visible(timeout=5000):
                logger.info("Clicking 'Unflag' button in Flag Details dialog")
                unflag_btn.click()
                self.page.wait_for_timeout(1000)
            else:
                save_btn = self.page.locator(self.FLAG_UNFLAG_SUBMIT_BUTTON).first
                if save_btn.is_visible(timeout=3000):
                    logger.info("Clicking savebutton in dialog")
                    save_btn.click()
                    self.page.wait_for_timeout(1000)
                else:
                    logger.info("Unmark icon click directly toggled the flight state")

            # 4. Wait for flight card to update to UNFLAGGED (mattooltip detached)
            logger.info(f"Waiting for flight '{flight_number}' to update to UNFLAGGED in DOM...")
            try:
                flight_card.locator(self.FLAGGED_FLIGHT_CSS).wait_for(state="detached", timeout=10000)
                logger.info(f"mattooltip='UnMark Flight' successfully detached for flight '{flight_number}'")
            except Exception:
                logger.warning("wait_for detached timed out, doing polling check...")
                for _ in range(6):
                    self.page.wait_for_timeout(1000)
                    if not self.is_flight_flagged(flight_card):
                        break

            self.page.wait_for_timeout(1000)

            # 5. Post-unflag check: Confirm mattooltip='UnMark Flight' is now ABSENT
            is_still_flagged = self.is_flight_flagged(flight_card)
            self.attach_screenshot(f"Unflagged_{flight_number}")

            if not is_still_flagged:
                logger.info(f"--- Successfully UNFLAGGED Flight: {flight_number} ---")
                return True
            else:
                logger.warning(f"Flight '{flight_number}' is STILL flagged after unflag attempt.")
                return False

    # ==================== CONDITIONAL FLAGGING / UNFLAGGING ====================
    def handle_flight_flag_state(self, flight_card, flag_name: str | None = None) -> dict:
        """
        Executes conditional flag/unflag based on current state:
        - If the flight is flagged -> Unflag the flight.
        - If the flight is not flagged -> Flag the flight.
        """
        flight_number = self.get_flight_number(flight_card)
        is_flagged = self.is_flight_flagged(flight_card)

        if is_flagged:
            logger.info(f"Flight '{flight_number}' is currently FLAGGED. Unflagging...")
            self.unflag_flight(flight_card)
            post_status = self.is_flight_flagged(flight_card)
            return {
                "flight_number": flight_number,
                "initial_state": "FLAGGED",
                "action": "UNFLAG",
                "verified": not post_status,
                "final_state": "UNFLAGGED" if not post_status else "FLAGGED"
            }
        else:
            logger.info(f"Flight '{flight_number}' is currently NOT FLAGGED. Flagging...")
            flag_res = self.flag_flight(flight_card, flag_name)
            post_status = self.is_flight_flagged(flight_card)
            return {
                "flight_number": flight_number,
                "initial_state": "UNFLAGGED",
                "action": "FLAG",
                "selected_flag": flag_res.get("selected_flag"),
                "available_flags": flag_res.get("available_flags"),
                "verified": post_status,
                "final_state": "FLAGGED" if post_status else "UNFLAGGED"
            }


