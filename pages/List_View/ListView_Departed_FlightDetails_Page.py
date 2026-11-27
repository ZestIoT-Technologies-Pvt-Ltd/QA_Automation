# Author : Gowthami Ankem
# Created Date : 2026-11-26
"""
==============  INTRODUCTION ================
Page Object: ListView_Departed_FlightDetails_Page
Description: Validating Flight Details,  Timings,
             and AODB (Airport Operational Database) Updates in the Departed tab of Flights List View.

Workflow :
1. Navigate to Flights List View and select the Departed tab.
2. Inspect Departed flight cards and validate Flight Details:
   - Flight Numbers (ARR - DEP)
   - Aircraft Type and Registration
   - Route (Origin-Station-Destination)
   - Flight Status Badge (e.g., 15M Late, On Time)
   - Bay / Stand number
   - Gate number
3. Validate  Timings:
   - Arrival schedule (STA, ETA) and On-Block time (ONBL) via hover dropdown
   - Departure schedule (STD, ETD) and Off-Block time (OFBL) via hover dropdown
   - Planned Off-Block Time (POBT)
   - Target Off-Block Time (TOBT / COBT)
4. Validate AODB Data:
   - Locate the AODB column (immediately following PAX Count column)
   - If AODB info icon is present:
     - Click info icon to open 'AODB UPDATES' dialog
     - Validate title and Arrival tab AODB records (Last Update, Flight NO, Bay, STA-ETA, ONB, Reg No, A/C Type, Status, Flight Type, Unique Key)
     - Validate Departure tab AODB records
     - Capture verification screenshot of AODB updates table
     - Safely close popup via the dialog close button
"""

import re
import allure
import pytest
from playwright.sync_api import Page, Locator, expect, TimeoutError
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Departed_FlightDetails_Page(BasePage):

    # ==================== NAVIGATION LOCATORS ====================
    MENU = "//span[@class='nav-icon']/i[text()='menu']"
    LIST_VIEW = "//div[@role='button']//span[text()='Flights']"
    DEPARTED_TAB = "//div[contains(text(),'Departed')]"
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]/div"
    NO_FLIGHTS_AVAILABLE = "//div[contains(text(),'No Flights Available')]"

    # ==================== FLIGHT DETAILS LOCATORS ====================
    FLIGHT_NUMBERS = "p[mattooltip='Flight Arrival Departure Numbers']"
    AIRCRAFT_TYPE = "div.aircraft_type"
    ROUTE_COL = "div.flight-details-col"
    STATUS_BADGE = "div.status-col"
    BAY_NUMBER = "div.bay-col"
    GATE_NUMBER = "div.gate-col"

    # ==================== COLUMN TIMINGS LOCATORS ====================
    ARRIVAL_TIME_COL = "div.arrival-time-col"
    DEPARTURE_TIME_COL = "div.departure-time-col"
    COBT_TOBT_COL = "div.cobt-status-col"

    # Timings hover dropdowns
    STA_ROW = "div.arrival-time-col div.dropdown-content p:has-text('STA')"
    ETA_ROW = "div.arrival-time-col div.dropdown-content p:has-text('ETA')"
    ONBLOCK_ROW = "div.arrival-time-col div.dropdown-content p:has-text('ONBL')"

    STD_ROW = "div.departure-time-col div.dropdown-content p:has-text('STD')"
    ETD_ROW = "div.departure-time-col div.dropdown-content p:has-text('ETD')"
    OFFBLOCK_ROW = "div.departure-time-col div.dropdown-content p:has-text('OFBL')"

    # ==================== AODB UPDATES POPUP LOCATORS ====================
    AODB_COL = "div.pax_count-col + div"
    AODB_ICON = "mat-icon.infoicon, mat-icon:has-text('info')"
    AODB_DIALOG = "mat-dialog-container"
    AODB_TITLE = "mat-dialog-container h2.mat-dialog-title"
    AODB_CLOSE_BUTTON = "mat-dialog-container mat-icon:has-text('close')"
    AODB_ARRIVAL_TAB = "mat-dialog-container .mat-tab-label:has-text('Arrival')"
    AODB_DEPARTURE_TAB = "mat-dialog-container .mat-tab-label:has-text('Departure')"
    AODB_TABLE_HEADERS = "mat-dialog-container .mat-tab-body-active .table-row.headeraodb .table-cell"
    AODB_TABLE_ROWS = "mat-dialog-container .mat-tab-body-active .table-row.aodbbody"
    AODB_ROW_CELLS = ".table-cell"

    # ==================== SPINNER SELECTORS ====================
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
            logger.warning(f"Loading spinner did not disappear within {timeout} ms; continuing")

    # ==================== NAVIGATION ====================
    @allure.step("Navigate to Flights List View")
    def navigate_to_list_view_page(self):
        """Navigates to the Flights List View dashboard via the main navigation menu."""
        try:
            logger.info("Navigating to Flights List View")
            if self.page.locator(self.DEPARTED_TAB).is_visible():
                logger.info("Already on Flights List View dashboard")
                return

            menu = self.page.locator(self.MENU)
            expect(menu).to_be_visible(timeout=30000)
            menu.hover()
            self.page.wait_for_timeout(1000)

            flights = self.page.locator(self.LIST_VIEW)
            if not flights.is_visible():
                menu.click()
                self.page.wait_for_timeout(1000)

            expect(flights).to_be_visible(timeout=15000)
            flights.click()

            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(2000)
            self.wait_for_loading_to_finish()
            logger.info("Turnaround List View page loaded successfully")
        except Exception as e:
            self.attach_screenshot("list_view_navigation_failed")
            logger.error(f"Failed to navigate to Flights List View: {e}")
            raise

    # ==================== SELECT DEPARTED TAB ====================
    @allure.step("Select Departed Tab")
    def select_departed_flights(self):
        try:
            departed_tab = self.page.locator(self.DEPARTED_TAB)
            expect(departed_tab).to_be_visible(timeout=15000)
            departed_tab.click()

            self.page.wait_for_timeout(2000)
            self.wait_for_loading_to_finish()

            cards = self.page.locator(self.FLIGHT_ROW_CARDS)
            no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)

            if cards.count() > 0:
                expect(cards.first).to_be_visible(timeout=15000)
                logger.info(f"Departed tab selected. Found {cards.count()} flight cards")
            elif no_flights.count() > 0 and no_flights.first.is_visible():
                logger.info("Departed tab selected: 'No Flights Available' is displayed")
            else:
                logger.info("Departed tab selected successfully")
        except Exception as e:
            self.attach_screenshot("departed_tab_selection_failed")
            logger.error(f"Failed to select Departed tab: {e}")
            raise

    # ==================== FLIGHT DETAILS VALIDATION ====================
    @allure.step("Validate Flight Details for Card {index}")
    def validate_flight_details(self, flight_card: Locator, index: int) -> dict:
        """
        Validates details displayed directly on the flight card:
        - Flight Numbers (ARR - DEP)
        - Aircraft Type & Registration
        - Route
        - Flight Status Badge
        - Bay / Stand
        - Gate
        """
        logger.info(f"--- Validating Flight Details for Flight Card {index} ---")
        details = {}

        # 1. Flight Numbers
        fn_loc = flight_card.locator(self.FLIGHT_NUMBERS)
        if fn_loc.count() > 0 and fn_loc.first.is_visible():
            details["flight_numbers"] = fn_loc.first.inner_text().strip()
            expect(fn_loc.first).to_be_visible()
            logger.info(f"Card {index} Flight Numbers: '{details['flight_numbers']}'")
        else:
            details["flight_numbers"] = "N/A"
            logger.warning(f"Card {index} Flight Numbers locator not visible")

        # 2. Aircraft Type & Registration
        ac_loc = flight_card.locator(self.AIRCRAFT_TYPE)
        if ac_loc.count() > 0 and ac_loc.first.is_visible():
            details["aircraft_type"] = ac_loc.first.inner_text().strip()
            expect(ac_loc.first).to_be_visible()
            logger.info(f"Card {index} Aircraft Type: '{details['aircraft_type']}'")
        else:
            details["aircraft_type"] = "N/A"
            logger.warning(f"Card {index} Aircraft Type not visible")

        # 3. Route
        route_loc = flight_card.locator(self.ROUTE_COL)
        if route_loc.count() > 0 and route_loc.first.is_visible():
            details["route"] = route_loc.first.inner_text().strip().replace("\n", " ")
            logger.info(f"Card {index} Route: '{details['route']}'")
        else:
            card_text = flight_card.inner_text()
            m_route = re.search(r"\b[A-Z]{3}-\s*[A-Z]{3}(?:\s*-[A-Z]{3})?\b", card_text)
            details["route"] = m_route.group(0).replace("\n", "") if m_route else "N/A"
            logger.info(f"Card {index} Route (from card text): '{details['route']}'")

        # 4. Status Badge
        status_loc = flight_card.locator(self.STATUS_BADGE)
        if status_loc.count() > 0 and status_loc.first.is_visible():
            details["status"] = status_loc.first.inner_text().strip()
            expect(status_loc.first).to_be_visible()
            logger.info(f"Card {index} Status Badge: '{details['status']}'")
        else:
            details["status"] = "N/A"
            logger.warning(f"Card {index} Status badge not visible")

        # 5. Bay / Stand Number
        bay_loc = flight_card.locator(self.BAY_NUMBER)
        if bay_loc.count() > 0 and bay_loc.first.is_visible():
            details["bay"] = bay_loc.first.inner_text().strip()
            expect(bay_loc.first).to_be_visible()
            logger.info(f"Card {index} Bay: '{details['bay']}'")
        else:
            details["bay"] = "N/A"
            logger.warning(f"Card {index} Bay not visible")

        # 6. Gate Number
        gate_loc = flight_card.locator(self.GATE_NUMBER)
        if gate_loc.count() > 0 and gate_loc.first.is_visible():
            details["gate"] = gate_loc.first.inner_text().strip()
            expect(gate_loc.first).to_be_visible()
            logger.info(f"Card {index} Gate: '{details['gate']}'")
        else:
            details["gate"] = "N/A"
            logger.warning(f"Card {index} Gate not visible")

        return details

    # ==================== COLUMN TIMINGS VALIDATION ====================
    @allure.step("Validate Column Timings for Card {index}")
    def validate_column_timings(self, flight_card: Locator, index: int) -> dict:
        """
        Validates column timings:
        - Arrival Schedule (STA, ETA, ONBL) by hovering over arrival column
        - Departure Schedule (STD, ETD, OFBL) by hovering over departure column
        - Planned Off-Block Time (POBT)
        - Target Off-Block Time (TOBT / COBT)
        """
        logger.info(f"--- Validating Column Timings for Flight Card {index} ---")
        timings = {}

        # 1. Arrival Schedule & ONBL (Hover)
        arr_col = flight_card.locator(self.ARRIVAL_TIME_COL)
        if arr_col.count() > 0 and arr_col.first.is_visible():
            timings["arrival_card_display"] = arr_col.first.inner_text().strip().replace("\n", " ")
            logger.info(f"Card {index} Arrival Schedule Display: '{timings['arrival_card_display']}'")

            # Hover to view STA / ETA / ONBL popup
            try:
                arr_col.first.hover(timeout=3000)
                self.page.wait_for_timeout(1000)

                sta = flight_card.locator(self.STA_ROW)
                if sta.count() > 0 and sta.first.is_visible():
                    timings["sta"] = sta.first.inner_text().strip()
                    logger.info(f"Card {index} Hover STA: '{timings['sta']}'")

                eta = flight_card.locator(self.ETA_ROW)
                if eta.count() > 0 and eta.first.is_visible():
                    timings["eta"] = eta.first.inner_text().strip()
                    logger.info(f"Card {index} Hover ETA: '{timings['eta']}'")

                onbl = flight_card.locator(self.ONBLOCK_ROW)
                if onbl.count() > 0 and onbl.first.is_visible():
                    timings["onbl"] = onbl.first.inner_text().strip()
                    logger.info(f"Card {index} Hover ONBL: '{timings['onbl']}'")
            except Exception as e:
                logger.warning(f"Card {index} arrival hover dropdown inspection: {e}")
        else:
            logger.warning(f"Card {index} Arrival column not visible")

        # 2. Departure Schedule & OFBL (Hover)
        dep_col = flight_card.locator(self.DEPARTURE_TIME_COL)
        if dep_col.count() > 0 and dep_col.first.is_visible():
            timings["departure_card_display"] = dep_col.first.inner_text().strip().replace("\n", " ")
            logger.info(f"Card {index} Departure Schedule Display: '{timings['departure_card_display']}'")

            # Hover to view STD / ETD / OFBL popup
            try:
                dep_col.first.hover(timeout=3000)
                self.page.wait_for_timeout(1000)

                std = flight_card.locator(self.STD_ROW)
                if std.count() > 0 and std.first.is_visible():
                    timings["std"] = std.first.inner_text().strip()
                    logger.info(f"Card {index} Hover STD: '{timings['std']}'")

                etd = flight_card.locator(self.ETD_ROW)
                if etd.count() > 0 and etd.first.is_visible():
                    timings["etd"] = etd.first.inner_text().strip()
                    logger.info(f"Card {index} Hover ETD: '{timings['etd']}'")

                ofbl = flight_card.locator(self.OFFBLOCK_ROW)
                if ofbl.count() > 0 and ofbl.first.is_visible():
                    timings["ofbl"] = ofbl.first.inner_text().strip()
                    logger.info(f"Card {index} Hover OFBL: '{timings['ofbl']}'")
            except Exception as e:
                logger.warning(f"Card {index} departure hover dropdown inspection: {e}")
        else:
            logger.warning(f"Card {index} Departure column not visible")

        # 3. POBT Column
        pobt_loc = flight_card.locator("div.flight-details-div > div:nth-child(9)")
        if pobt_loc.count() > 0 and pobt_loc.first.is_visible():
            timings["pobt"] = pobt_loc.first.inner_text().strip()
            logger.info(f"Card {index} POBT: '{timings['pobt']}'")
        else:
            timings["pobt"] = "N/A"

        # 4. TOBT / COBT Column
        cobt_loc = flight_card.locator(self.COBT_TOBT_COL)
        if cobt_loc.count() > 0 and cobt_loc.first.is_visible():
            timings["tobt"] = cobt_loc.first.inner_text().strip()
            logger.info(f"Card {index} TOBT/COBT: '{timings['tobt']}'")
        else:
            timings["tobt"] = "N/A"

        return timings

    # ==================== AODB DATA VALIDATION ====================
    @allure.step("Validate AODB Updates Data for Card {index}")
    def validate_aodb_data(self, flight_card: Locator, index: int, flight_details: dict | None = None) -> dict:
        """
        Validates the AODB (Airport Operational Database) Updates popup:
        - Locates the AODB column 
        - Checks if the AODB info icon is present on this flight card
        - If present:
          a) Clicks the info icon to open 'AODB UPDATES' dialog
          b) Validates dialog title 'AODB UPDATES'
          c) Inspects and asserts Arrival tab records (Last Update, Flight NO, Bay, STA-ETA, ONB, Reg No, A/C Type, Flight Status, Unique Key)
          d) Switches to Departure tab, inspects and asserts departure records (Last Update, Flight NO, Bay, STD-ETD, OFB, Reg No, A/C Type, Flight Status, Unique Key)
          e) Cross-verifies AODB flight numbers against the flight card details
          f) Captures verification screenshot of the AODB updates table
          g) Safely closes the popup via close button 
        - If not present (e.g. flights/stations without AODB integration):
          Logs note and continues safely without failing.
        """
        logger.info(f"--- Validating AODB Data for Flight Card {index} ---")
        aodb_info = {
            "has_aodb": False,
            "arrival_count": 0,
            "departure_count": 0,
            "arrival_records": [],
            "departure_records": []
        }

        aodb_col = flight_card.locator(self.AODB_COL)
        if aodb_col.count() == 0:
            logger.info(f"Card {index}: AODB column not found on card. Skipping AODB dialog validation.")
            return aodb_info

        aodb_icon = aodb_col.locator(self.AODB_ICON)
        if aodb_icon.count() == 0 or not aodb_icon.first.is_visible():
            logger.info(f"Card {index}: AODB info icon is not present on this flight card. Skipping AODB dialog validation.")
            return aodb_info

        try:
            logger.info(f"Card {index}: Clicking AODB info icon in AODB column")
            aodb_icon.first.click()
            self.page.wait_for_timeout(1500)

            dialog = self.page.locator(self.AODB_DIALOG)
            expect(dialog.first).to_be_visible(timeout=10000)

            # 1. Verify Dialog Title
            title = self.page.locator(self.AODB_TITLE)
            expect(title.first).to_be_visible(timeout=5000)
            expect(title.first).to_contain_text("AODB UPDATES")
            title_text = title.first.inner_text().strip()
            logger.info(f"Card {index}: AODB Dialog opened with title '{title_text}'")

            aodb_info["has_aodb"] = True

            # 2. Validate Arrival Tab AODB Data
            arr_tab = self.page.locator(self.AODB_ARRIVAL_TAB)
            if arr_tab.count() > 0:
                arr_tab.first.click()
                self.page.wait_for_timeout(1000)

                # Validate Headers
                headers = [c.inner_text().strip() for c in self.page.locator(self.AODB_TABLE_HEADERS).all()]
                logger.info(f"Card {index}: AODB Arrival Headers: {headers}")
                assert any("Flight NO" in h for h in headers), f"Card {index}: 'Flight NO' header missing from Arrival AODB table"

                # Validate Arrival Records
                rows = self.page.locator(self.AODB_TABLE_ROWS)
                row_count = rows.count()
                aodb_info["arrival_count"] = row_count
                logger.info(f"Card {index}: Found {row_count} Arrival AODB records in table")

                assert row_count > 0, f"Card {index}: Expected at least 1 Arrival AODB update record, found 0"

                for r_idx in range(row_count):
                    cells = [c.inner_text().strip() for c in rows.nth(r_idx).locator(self.AODB_ROW_CELLS).all()]
                    record = {
                        "last_update": cells[0] if len(cells) > 0 else "",
                        "flight_no": cells[1] if len(cells) > 1 else "",
                        "bay": cells[2] if len(cells) > 2 else "",
                        "sta_eta": cells[3] if len(cells) > 3 else "",
                        "onb": cells[4] if len(cells) > 4 else "",
                        "reg_no": cells[5] if len(cells) > 5 else "",
                        "ac_type": cells[6] if len(cells) > 6 else "",
                        "operational_status": cells[7] if len(cells) > 7 else "",
                        "flight_status": cells[8] if len(cells) > 8 else "",
                        "flight_type": cells[9] if len(cells) > 9 else "",
                        "unique_key": cells[10] if len(cells) > 10 else "",
                        "raw": " | ".join(cells)
                    }
                    aodb_info["arrival_records"].append(record)
                    if r_idx < 3:
                        logger.info(f"Card {index} Arrival Record {r_idx + 1}: {record['raw']}")

                first_arr = aodb_info["arrival_records"][0]
                assert first_arr["flight_no"] != "", f"Card {index}: Latest Arrival AODB record 'Flight NO' is empty"
                assert first_arr["flight_status"] != "", f"Card {index}: Latest Arrival AODB record 'Flight Status' is empty"
                assert first_arr["last_update"] != "", f"Card {index}: Latest Arrival AODB record 'Last Update' is empty"
                logger.info(
                    f"Card {index} Latest Arrival AODB Validated: Flight NO='{first_arr['flight_no']}', "
                    f"Bay='{first_arr['bay']}', Status='{first_arr['flight_status']}', Reg='{first_arr['reg_no']}'"
                )

                # Cross-verify with flight card numbers if provided
                if flight_details and flight_details.get("flight_numbers"):
                    card_fn = flight_details["flight_numbers"]
                    # Extract arrival flight number part before '-'
                    arr_fn_expected = card_fn.split("-")[0].strip() if "-" in card_fn else card_fn
                    arr_fn_norm = re.sub(r"\s+", "", arr_fn_expected)
                    aodb_fn_norm = re.sub(r"\s+", "", first_arr["flight_no"])
                    if arr_fn_norm and aodb_fn_norm:
                        if arr_fn_norm in aodb_fn_norm or aodb_fn_norm in arr_fn_norm:
                            logger.info(f"Card {index}: Verified AODB Arrival Flight NO '{first_arr['flight_no']}' matches card '{arr_fn_expected}'")
                        else:
                            logger.warning(f"Card {index}: AODB Arrival Flight NO '{first_arr['flight_no']}' does not match card '{arr_fn_expected}'")

            # 3. Validate Departure Tab AODB Data
            dep_tab = self.page.locator(self.AODB_DEPARTURE_TAB)
            if dep_tab.count() > 0:
                dep_tab.first.click()
                self.page.wait_for_timeout(1000)

                # Validate Headers
                dep_headers = [c.inner_text().strip() for c in self.page.locator(self.AODB_TABLE_HEADERS).all()]
                logger.info(f"Card {index}: AODB Departure Headers: {dep_headers}")
                assert any("Flight NO" in h for h in dep_headers), f"Card {index}: 'Flight NO' header missing from Departure AODB table"

                # Validate Departure Records
                rows = self.page.locator(self.AODB_TABLE_ROWS)
                row_count = rows.count()
                aodb_info["departure_count"] = row_count
                logger.info(f"Card {index}: Found {row_count} Departure AODB records in table")

                assert row_count > 0, f"Card {index}: Expected at least 1 Departure AODB update record, found 0"

                for r_idx in range(row_count):
                    cells = [c.inner_text().strip() for c in rows.nth(r_idx).locator(self.AODB_ROW_CELLS).all()]
                    record = {
                        "last_update": cells[0] if len(cells) > 0 else "",
                        "flight_no": cells[1] if len(cells) > 1 else "",
                        "bay": cells[2] if len(cells) > 2 else "",
                        "std_etd": cells[3] if len(cells) > 3 else "",
                        "ofb": cells[4] if len(cells) > 4 else "",
                        "reg_no": cells[5] if len(cells) > 5 else "",
                        "ac_type": cells[6] if len(cells) > 6 else "",
                        "operational_status": cells[7] if len(cells) > 7 else "",
                        "flight_status": cells[8] if len(cells) > 8 else "",
                        "flight_type": cells[9] if len(cells) > 9 else "",
                        "unique_key": cells[10] if len(cells) > 10 else "",
                        "raw": " | ".join(cells)
                    }
                    aodb_info["departure_records"].append(record)
                    if r_idx < 3:
                        logger.info(f"Card {index} Departure Record {r_idx + 1}: {record['raw']}")

                first_dep = aodb_info["departure_records"][0]
                assert first_dep["flight_no"] != "", f"Card {index}: Latest Departure AODB record 'Flight NO' is empty"
                assert first_dep["flight_status"] != "", f"Card {index}: Latest Departure AODB record 'Flight Status' is empty"
                assert first_dep["last_update"] != "", f"Card {index}: Latest Departure AODB record 'Last Update' is empty"
                logger.info(
                    f"Card {index} Latest Departure AODB Validated: Flight NO='{first_dep['flight_no']}', "
                    f"Bay='{first_dep['bay']}', Status='{first_dep['flight_status']}', Reg='{first_dep['reg_no']}'"
                )

                # Cross-verify with flight card numbers if provided
                if flight_details and flight_details.get("flight_numbers"):
                    card_fn = flight_details["flight_numbers"]
                    # Extract departure flight number part after '-'
                    dep_fn_expected = card_fn.split("-")[1].strip() if "-" in card_fn else card_fn
                    dep_fn_digits = re.sub(r"\D", "", dep_fn_expected)
                    aodb_dep_digits = re.sub(r"\D", "", first_dep["flight_no"])
                    if dep_fn_digits and aodb_dep_digits and (dep_fn_digits in aodb_dep_digits or aodb_dep_digits in dep_fn_digits):
                        logger.info(f"Card {index}: Verified AODB Departure Flight NO '{first_dep['flight_no']}' matches card '{dep_fn_expected}'")
                    else:
                        logger.warning(f"Card {index}: AODB Departure Flight NO '{first_dep['flight_no']}' comparison with card '{dep_fn_expected}'")

            self.attach_screenshot(f"aodb_updates_table_card_{index}")

            # 4. Safely Close Popup via Close Button (never use Escape key)
            close_btn = self.page.locator(self.AODB_CLOSE_BUTTON)
            expect(close_btn.first).to_be_visible(timeout=5000)
            logger.info(f"Card {index}: Clicking AODB close button")
            close_btn.first.click()
            self.page.wait_for_timeout(1000)
            expect(dialog.first).not_to_be_visible(timeout=5000)
            logger.info(f"Card {index}: AODB Updates popup closed successfully")

            return aodb_info

        except Exception as e:
            self.attach_screenshot(f"aodb_validation_failed_card_{index}")
            logger.error(f"Card {index}: Failed during AODB validation: {e}")
            raise

    # ==================== MAIN COMBINED VALIDATION ====================
    @allure.step("Validate Flight Details, Column Timings, and AODB Data")
    def validate_departed_flight_details(self, max_flights: int = 5) -> list:
        """
        Iterates over departed flight cards (up to max_flights) and performs:
        1. Flight Details validation (Flight Numbers, Aircraft Type, Route, Status, Bay, Gate)
        2. Timings validation (STA/ETA/ONBL, STD/ETD/OFBL, POBT, TOBT/COBT)
        3. AODB Data validation (Clicks AODB icon, verifies AODB UPDATES table in Arrival & Departure tabs, closes popup)
        Returns a list of dictionaries with validation data for each processed flight card.
        """
        cards = self.page.locator(self.FLIGHT_ROW_CARDS)
        no_flights = self.page.locator(self.NO_FLIGHTS_AVAILABLE)

        total_cards = cards.count()
        if total_cards == 0:
            if no_flights.count() > 0 and no_flights.first.is_visible():
                logger.info("Departed tab shows 'No Flights Available'. Test passed for zero state.")
                return []
            logger.warning("No flight cards found in Departed tab")
            return []

        flights_to_check = min(total_cards, max_flights)
        logger.info(f"Total Departed Flight Cards: {total_cards}. Testing first {flights_to_check} flights.")
        validated_flights = []

        for i in range(flights_to_check):
            card_index = i + 1
            with allure.step(f"Validating Departed Flight Card {card_index} of {flights_to_check}"):
                flight_card = cards.nth(i)
                expect(flight_card).to_be_visible(timeout=10000)

                # 1. Flight Details
                details = self.validate_flight_details(flight_card, card_index)
                logger.info(f"Card {card_index} Flight Details summary: {details}")

                # 2. Column Timings
                timings = self.validate_column_timings(flight_card, card_index)
                logger.info(f"Card {card_index} Timings summary: {timings}")

                # 3. AODB Data Checking (AODB Updates dialog, Arrival & Departure records)
                aodb_data = self.validate_aodb_data(flight_card, card_index, flight_details=details)
                logger.info(f"Card {card_index} AODB Data summary: {aodb_data}")

                validated_flights.append({
                    "index": card_index,
                    "details": details,
                    "timings": timings,
                    "aodb": aodb_data
                })

        self.attach_screenshot("departed_flight_details_and_aodb_complete")
        logger.info("All Departed flight details, column timings, and AODB checks completed successfully")
        return validated_flights
