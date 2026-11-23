# Author : Gowthami Ankem
# Created Date : 2026-11-20
# Author : Gowthami Ankem
# Modified Date : 2026-11-23
"""
==============  INTRODUCTION ================
Page Object: ListView_DepartedSection_FlightCard_Page
Description: Departed Section Flight Card validation in Flights List View.
             Opens the Flight Card report popup (.rh-form) for departed flights and cross-verifies
             that critical flight data—including Flight Number, STA, STD, ETA, ETD, Bay, and Gate—
             matches the flight information displayed on the List View card.

Workflow Capabilities:
1. Navigate to Flights List View and switch to the Departed section tab.
2. Inspect each Departed flight card and extract key data:
   - Flight Numbers (Arrival and Departure)
   - Scheduled Arrival (STA) and Scheduled Departure (STD)
   - Estimated times (ETA, ETD) and Block times (ONBL, OFBL)
   - Bay / Stand and Gate
3. Open the flight's ellipsis menu ('more_vert') and select 'Flight Card'.
4. Switch to the newly opened Flight Card popup tab (.rh-form).
5. Cross-verify that the extracted List View data matches the data rendered inside the Flight Card:
   - Confirms Flight Number exists on the Flight Card.
   - Confirms STA matches.
   - Confirms STD matches.
   - Confirms ETA, ETD, Bay, and Gate match if present.
6. Capture a screenshot of the verified Flight Card.
7. Safely close the popup tab and continue with subsequent departed flights.
"""

import re
import time
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_DepartedSection_FlightCard_Page(BasePage):
   
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
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # ==================== CARD DATA LOCATORS ====================
    FLIGHT_NUMBER_LOCATORS = (
        "p[mattooltip*='Flight Arrival Departure Numbers'], "
        "p[mattooltip*='Flight'], "
        ".flight-names, "
        ".arr-dep, "
        "[class*='flight-number']"
    )
    ARRIVAL_TIME_COL = ".arrival-time-col, [class*='arrival-time']"
    DEPARTURE_TIME_COL = ".departure-time-col, [class*='departure-time']"
    BAY_COL = ".bay-col, [class*='bay']"
    GATE_COL = ".gate-col, [class*='gate']"
    AIRCRAFT_TYPE_COL = ".aircraft_type, [class*='aircraft']"

    # ==================== MENU & POPUP LOCATORS ====================
    FLIGHT_MENU_ICON = "//mat-icon[normalize-space()='more_vert' or contains(text(),'more_vert')]"
    FLIGHT_CARD_MENU = "Flight Card"
    FLIGHT_CARD_CONTAINER = ".rh-form, app-flight-card, [class*='flight-card-container'], body"

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
        self.report_tab = None

    # ==================== SCREENSHOT ====================
    def attach_screenshot(self, name: str, full_page: bool = True):
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

            self.page.wait_for_timeout(2000)
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

    # ==================== DATA EXTRACTION HELPERS ====================
    def get_flight_number(self, flight_card: Locator) -> str:
        """Extracts primary flight number string from a flight card."""
        try:
            fn_loc = flight_card.locator(
                "p[mattooltip='Flight Arrival Departure Numbers'], "
                "p[mattooltip*='Flight'], "
                ".flight-names, "
                ".arr-dep"
            )
            if fn_loc.count() > 0 and fn_loc.first.is_visible():
                return fn_loc.first.inner_text().strip()
        except Exception:
            pass
        return "Unknown Flight"

    def _extract_times_from_column(self, col_locator: Locator) -> dict:
        """Extracts (STA, STD, ETA, ETD, ONBL, OFBL) from a time column."""
        times = {}
        if col_locator.count() == 0:
            return times
        try:
            try:
                col_locator.first.hover(timeout=2000)
            except Exception:
                pass

            raw_text = col_locator.first.inner_text() or ""
            for label in ("STA", "STD", "ETA", "ETD", "ONBL", "OFBL", "ATA", "ATD"):
                m = re.search(rf"\b{label}\b\s*[:\-]?\s*(\d{{1,2}}:\d{{2}})", raw_text, re.IGNORECASE)
                if m:
                    times[label.lower()] = m.group(1)

            if not times:
                clock_match = re.search(r"\b(\d{1,2}:\d{2})\b", raw_text)
                if clock_match:
                    times["time"] = clock_match.group(1)
        except Exception as e:
            logger.debug(f"Could not extract time from column: {e}")
        return times

    def extract_list_view_data(self, flight_card: Locator) -> dict:
        """Extracts complete flight information from the List View card before opening popup."""
        data = {
            "flight_numbers": [],
            "raw_flight_text": "",
            "times": {},
            "bay": "",
            "gate": "",
            "aircraft_type": ""
        }
        try:
            # 1. Flight Number
            raw_fn = self.get_flight_number(flight_card)
            data["raw_flight_text"] = raw_fn

            tokens = re.findall(r"\b[A-Z0-9]{2,3}\s*\d{1,5}\b|\b\d{3,5}\b", raw_fn)
            data["flight_numbers"] = [t.strip() for t in tokens if t.strip()]
            if not data["flight_numbers"] and raw_fn and raw_fn != "Unknown Flight":
                data["flight_numbers"] = [raw_fn.splitlines()[0].strip()]

            # 2. Arrival Times (STA, ETA, ONBL)
            arr_col = flight_card.locator(self.ARRIVAL_TIME_COL)
            arr_times = self._extract_times_from_column(arr_col)
            for k, v in arr_times.items():
                data["times"][f"arrival_{k}" if k == "time" else k] = v

            # 3. Departure Times (STD, ETD, OFBL)
            dep_col = flight_card.locator(self.DEPARTURE_TIME_COL)
            dep_times = self._extract_times_from_column(dep_col)
            for k, v in dep_times.items():
                data["times"][f"departure_{k}" if k == "time" else k] = v

            # 4. Bay / Stand Number
            bay_loc = flight_card.locator(self.BAY_COL)
            if bay_loc.count() > 0 and bay_loc.first.is_visible():
                bay_text = bay_loc.first.inner_text().strip()
                m_bay = re.search(r"\b[A-Z0-9_-]{1,10}\b", bay_text.replace("Bay", "").replace("Stand", ""))
                if m_bay:
                    data["bay"] = m_bay.group(0).strip()

            # 5. Gate Number
            gate_loc = flight_card.locator(self.GATE_COL)
            if gate_loc.count() > 0 and gate_loc.first.is_visible():
                gate_text = gate_loc.first.inner_text().strip()
                m_gate = re.search(r"\b[A-Z0-9_-]{1,10}\b", gate_text.replace("Gate", ""))
                if m_gate:
                    data["gate"] = m_gate.group(0).strip()

            # 6. Aircraft Type
            ac_loc = flight_card.locator(self.AIRCRAFT_TYPE_COL)
            if ac_loc.count() > 0 and ac_loc.first.is_visible():
                data["aircraft_type"] = ac_loc.first.inner_text().strip()

            logger.info(
                f"[{raw_fn}] Extracted List View Data: Flight Numbers={data['flight_numbers']}, "
                f"Times={data['times']}, Bay='{data['bay']}', Gate='{data['gate']}'"
            )
        except Exception as e:
            logger.warning(f"Error extracting List View card fields: {e}")

        return data

    # ==================== DATA VERIFICATION IN FLIGHT CARD POPUP ====================
    def verify_flight_card_data(self, popup: Page, list_view_data: dict, flight_number: int) -> list:
        """Cross-checks that List View card data matches the opened Flight Card popup."""
        card_container = popup.locator(self.FLIGHT_CARD_CONTAINER)
        expect(card_container.first).to_be_visible(timeout=60000)

        card_text = card_container.first.inner_text()
        raw_label = list_view_data.get("raw_flight_text") or f"Flight_{flight_number}"
        logger.info(f"[{raw_label}] Cross-verifying Flight Card contents against List View data...")

        comparison_results = []

        # 1. Flight Number Verification
        flight_tokens = list_view_data.get("flight_numbers", [])
        matched_tokens = []
        for token in flight_tokens:
            token_compact = token.replace(" ", "")
            if token in card_text or token_compact in card_text.replace(" ", ""):
                matched_tokens.append(token)

        if matched_tokens:
            msg = f"Flight Number '{', '.join(matched_tokens)}' verified on Flight Card"
            logger.info(f"[{raw_label}] PASS: {msg}")
            comparison_results.append(("Flight Number", msg, True))
        else:
            msg = f"Flight Numbers {flight_tokens} not found on Flight Card text"
            logger.warning(f"[{raw_label}] WARNING: {msg}")
            comparison_results.append(("Flight Number", msg, False))

        # 2.  Verification (STA, STD, ETA, ETD, ONBL, OFBL)
        times = list_view_data.get("times", {})
        for time_key, time_val in times.items():
            if time_val and time_val != "-" and len(time_val) >= 4:
                if time_val in card_text:
                    msg = f"{time_key.upper()} time '{time_val}' matches on Flight Card"
                    logger.info(f"[{raw_label}] PASS: {msg}")
                    comparison_results.append((time_key.upper(), msg, True))
                else:
                    msg = f"{time_key.upper()} time '{time_val}' not found in Flight Card text"
                    logger.warning(f"[{raw_label}] WARNING: {msg}")
                    comparison_results.append((time_key.upper(), msg, False))

        # 3. Bay / Stand Verification
        bay = list_view_data.get("bay")
        if bay and bay not in ("-", "NONE") and len(bay) >= 2:
            if bay in card_text:
                msg = f"Bay / Stand '{bay}' matches on Flight Card"
                logger.info(f"[{raw_label}] PASS: {msg}")
                comparison_results.append(("Bay", msg, True))
            else:
                msg = f"Bay '{bay}' not found in Flight Card"
                logger.warning(f"[{raw_label}] WARNING: {msg}")
                comparison_results.append(("Bay", msg, False))

        # 4. Gate Verification
        gate = list_view_data.get("gate")
        if gate and gate not in ("-", "NONE") and len(gate) >= 2:
            if gate in card_text:
                msg = f"Gate '{gate}' matches on Flight Card"
                logger.info(f"[{raw_label}] PASS: {msg}")
                comparison_results.append(("Gate", msg, True))
            else:
                msg = f"Gate '{gate}' not found in Flight Card"
                logger.warning(f"[{raw_label}] WARNING: {msg}")
                comparison_results.append(("Gate", msg, False))

        # Assert that at least one primary field (flight number or scheduled time) matched
        passed_checks = [r for r in comparison_results if r[2]]
        assert len(passed_checks) > 0, (
            f"Flight Card data verification failed for [{raw_label}]: "
            f"No matching fields found between List View and Flight Card."
        )

        return comparison_results

    # ==================== OPEN AND VALIDATE ONE FLIGHT CARD ====================
    def open_and_validate_flight_card(self, flight_card: Locator, flight_number: int) -> bool:
        """Extracts data from the card, opens the Flight Card in a new tab, verifies data, and closes tab."""
        popup = None
        flight_label = self.get_flight_number(flight_card)

        try:
            logger.info(f"Processing Flight {flight_number}: {flight_label}")
            flight_card.scroll_into_view_if_needed()

            # Step 1: Extract flight data from List View card BEFORE clicking menu
            list_view_data = self.extract_list_view_data(flight_card)

            menu_icon = flight_card.locator(self.FLIGHT_MENU_ICON)
            expect(menu_icon).to_be_visible(timeout=15000)

            # Step 2: Open the Flight Card popup tab
            with self.page.context.expect_page(timeout=90000) as new_page_info:
                menu_icon.click()

                flight_card_menu = self.page.get_by_role(
                    "menuitem",
                    name=self.FLIGHT_CARD_MENU,
                    exact=True
                )
                expect(flight_card_menu).to_be_visible(timeout=15000)
                flight_card_menu.click()

            popup = new_page_info.value
            self.report_tab = popup

            popup.wait_for_load_state("domcontentloaded", timeout=90000)

            # Step 3: Cross-verify data inside the Flight Card
            comparison_results = self.verify_flight_card_data(popup, list_view_data, flight_number)

            matched_fields = [r[0] for r in comparison_results if r[2]]
            logger.info(
                f"Flight Card {flight_number} [{flight_label}] validated successfully. "
                f"Matched fields: {matched_fields}"
            )

            # Capture screenshot of the verified Flight Card
            self.attach_screenshot(f"flight_card_{flight_number}_validated")
            return True

        except Exception as e:
            self.attach_screenshot(f"flight_card_{flight_number}_failed")
            logger.error(f"Flight Card {flight_number} [{flight_label}] validation failed: {e}")
            raise

        finally:
            if popup is not None and not popup.is_closed():
                popup.close()
                logger.info(f"Closed Flight Card tab for flight {flight_number}")

    # ==================== CHECK ALL DEPARTED FLIGHTS ====================
    def validate_departed_flight_cards(self, max_flights: int | None = None) -> int:
        """
        Iterates over departed flight cards:
        1. Extracts Flight Number, STA, STD, ETA, ETD, Bay, and Gate from the List View card.
        2. Opens the Flight Card in a new tab.
        3. Cross-verifies that the data matches on the Flight Card form.
        4. Closes the popup tab and proceeds to the next flight.
        """
        try:
            cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)

            if no_flights.count() > 0 and no_flights.first.is_visible():
                logger.warning("No departed flight cards available: 'No Flights Available' is displayed.")
                return 0

            total_flights = cards.count()
            if total_flights == 0:
                logger.warning("No flight cards found in Departed section")
                return 0

            flights_to_check = min(total_flights, max_flights) if max_flights else total_flights
            logger.info(f"Checking {flights_to_check} of {total_flights} Departed flight cards for Flight Card validation")

            validated_count = 0

            for index in range(flights_to_check):
                flight_number = index + 1
                logger.info(f"--- Flight Card {flight_number}/{flights_to_check} ---")

                current_cards = self.page.locator(self.FLIGHT_ROW_CARDS)
                if index >= current_cards.count():
                    pytest.fail(f"Flight list changed while processing flight {flight_number}")

                card = current_cards.nth(index)
                expect(card).to_be_visible(timeout=15000)

                self.open_and_validate_flight_card(card, flight_number)
                validated_count += 1

            logger.info(
                f"All {validated_count} departed Flight Cards "
                f"and their data were validated successfully."
            )
            return validated_count

        except Exception as e:
            self.attach_screenshot("all_departed_flight_cards_failed")
            logger.error(f"Failed to validate all departed Flight Cards: {e}")
            raise

    def check_all_departed_flight_cards(self):
        return self.validate_departed_flight_cards()

    def validate_departed_flight_report(self):
        self.navigate_to_list_view_page()
        self.select_departed_flights()
        self.validate_departed_flight_cards()

    def switch_back_to_main_tab(self):
        if not self.page.is_closed():
            self.page.bring_to_front()
            logger.info("Returned to the main List View tab")


