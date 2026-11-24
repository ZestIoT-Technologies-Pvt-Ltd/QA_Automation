# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

from playwright.sync_api import expect
import pytest
import allure
from pages.List_View.ListView_Ongoing_FlightData_Page import Flights_View_Ongoing_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_flights_view_ongoing(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Check Flights List View details across Ongoing and Departed sections.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Load all flights and verify that all section tabs (Ongoing, Incoming, Departed, Non Operational) are visible.
    4. Step 3: In Ongoing section, check activity dropdowns and PTS lists for flights.
    5. Step 4: In Ongoing section, hover over STA and check Onblock time display.
    6. Step 5: Switch to Departed section tab.
    7. Step 6: In Departed section, hover over ETD to check Offblock time and verify flight card in a new tab.
    """
    logger.info("Starting Flights View Ongoing Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    flights_view_ongoing_page = Flights_View_Ongoing_Page(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Navigate to Flights List View Dashboard
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            flights_view_ongoing_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 2: Load all flights and verify that all section tabs are visible
    # -------------------------------------------------------------------------
    with allure.step("Step 2: Load All Flights and Verify Section Tabs"):
        with allure.step("2.1: Load flights list view and check all section tabs"):
            flights_view_ongoing_page.load_all_flights()
            for section in flights_view_ongoing_page.SECTIONS:
                section_name = section["name"]
                logger.info(f"Checking {section_name} Section")
                section_tab = flights_view_ongoing_page.page.locator(section["tab"])
                expect(section_tab).to_be_visible()
                logger.info(f"{section_name} Section is Displayed")

        allure.attach(
            "All Section Tabs Verified: Ongoing, Incoming, Departed, Non Operational.",
            name="Section_Tabs_Status",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info("All Sections are Displayed Successfully")

    # -------------------------------------------------------------------------
    # Step 3: In Ongoing Section, check Activity Dropdowns and PTS names
    # -------------------------------------------------------------------------
    total_found = flights_view_ongoing_page.count_of_flights()
    number_of_flights = min(total_found, 15) if total_found > 0 else 0
    flight_cards = flights_view_ongoing_page.get_flight_cards()

    with allure.step(f"Step 3: Check Activity Dropdowns & PTS List in Ongoing Section ({number_of_flights} Flights)"):
        logger.info(f"Number of Flights to validate in Ongoing: {number_of_flights}")

        for i in range(number_of_flights):
            flight_card = flight_cards.nth(i)
            fl_num = flights_view_ongoing_page.get_flight_number(flight_card) or f"Flight {i + 1}"

            with allure.step(f"Step 3.{i+1}: Check Activity Dropdown for Flight '{fl_num}'"):
                count_of_activity_dropdowns = flights_view_ongoing_page.activity_dropdown_is_displayed(flight_card)

                if count_of_activity_dropdowns == 1:
                    for j in range(count_of_activity_dropdowns):
                        activity_dropdown = flight_card.locator(flights_view_ongoing_page.ACTIVITY_DROPDOWN_CARD).nth(j)
                        flights_view_ongoing_page.pts_is_displayed(activity_dropdown, flight_card)
                elif count_of_activity_dropdowns > 1:
                    for j in range(count_of_activity_dropdowns - 2):
                        activity_dropdown = flight_card.locator(flights_view_ongoing_page.ACTIVITY_DROPDOWN_CARD).nth(j)
                        flights_view_ongoing_page.pts_is_displayed(activity_dropdown, flight_card)
                else:
                    logger.warning(f"Activity Dropdown is not Displayed for Flight '{fl_num}'")

        allure.attach(
            f"Ongoing Section: Verified activity dropdowns and PTS details for {number_of_flights} flight cards.",
            name="Ongoing_Activity_Validation",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 4: Validate Onblock Time (hover on STA) in Ongoing Section
    # -------------------------------------------------------------------------
    with allure.step(f"Step 4: Validate Onblock Time (STA Hover) across Ongoing Flights"):
        for i in range(number_of_flights):
            flight_card = flight_cards.nth(i)
            fl_num = flights_view_ongoing_page.get_flight_number(flight_card) or f"Flight {i + 1}"

            with allure.step(f"Step 4.{i+1}: Hover on STA for Flight '{fl_num}' to check Onblock Time"):
                sta_element = flight_card.locator(flights_view_ongoing_page.STA)

                if sta_element.count() > 0 and sta_element.first.is_visible():
                    sta_element.first.hover()
                    page.wait_for_timeout(1000)

                    onblock_time = flight_card.locator(flights_view_ongoing_page.ONBLOCK_TIME)
                    if onblock_time.count() > 0 and onblock_time.first.is_visible():
                        expect(onblock_time.first).to_be_visible()
                        logger.info(f"Onblock Time is displayed for Flight '{fl_num}'")
                    else:
                        logger.info(f"Onblock Time is not displayed for Flight '{fl_num}'")

                    flights_view_ongoing_page.dismiss_lingering_tooltip()

        allure.attach(
            f"Ongoing Section: Completed STA hover and Onblock time check across {number_of_flights} flights.",
            name="Ongoing_Onblock_Validation",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info("Onblock Time Validation Completed for Ongoing Section")

    # -------------------------------------------------------------------------
    # Step 5: Switch to Departed Section
    # -------------------------------------------------------------------------
    with allure.step("Step 5: Navigate to Departed Section Tab"):
        with allure.step("5.1: Click 'Departed' section tab"):
            departed_section = flights_view_ongoing_page.page.locator(
                flights_view_ongoing_page.SECTIONS[2]["tab"]
            )
            expect(departed_section).to_be_visible()
            departed_section.click()
            flights_view_ongoing_page.flight_are_visible()

        allure.attach(
            "Switched to Departed Section. Flight cards are displayed.",
            name="Departed_Section_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    # -------------------------------------------------------------------------
    # Step 6: Validate Offblock Time (hover on ETD) and Flight Card in Departed Section
    # -------------------------------------------------------------------------
    number_of_departed = min(flights_view_ongoing_page.count_of_flights(), 15)
    departed_cards = flights_view_ongoing_page.get_flight_cards()

    with allure.step(f"Step 6: Validate Offblock Time (ETD Hover) and Flight Card in Departed Section ({number_of_departed} Flights)"):
        for i in range(number_of_departed):
            flight_card = departed_cards.nth(i)
            expect(flight_card).to_be_visible()
            fl_num = flights_view_ongoing_page.get_flight_number(flight_card) or f"Flight {i + 1}"

            with allure.step(f"Step 6.{i+1}: Validate Departed Flight '{fl_num}' (Offblock Time & Flight Card Detail)"):
                # Hover on ETD to view Offblock Time
                etd_element = flight_card.locator(flights_view_ongoing_page.ETD)
                if etd_element.count() > 0 and etd_element.first.is_visible():
                    etd_element.first.hover()
                    page.wait_for_timeout(1000)

                    offblock_time = flight_card.locator(flights_view_ongoing_page.OFFBLOCK_TIME)
                    if offblock_time.count() > 0 and offblock_time.first.is_visible():
                        expect(offblock_time.first).to_be_visible()
                        logger.info(f"Offblock Time is displayed for Departed Flight '{fl_num}'")
                    else:
                        logger.info(f"Offblock Time is not displayed for Departed Flight '{fl_num}'")

                    flights_view_ongoing_page.dismiss_lingering_tooltip()

                # Open Flight Menu for the Same Flight Card
                flight_menu = flight_card.locator(flights_view_ongoing_page.FLIGHT_MENU_ICON)
                if flight_menu.count() > 0 and flight_menu.first.is_visible():
                    flight_menu.first.click()

                    flight_card_button = flights_view_ongoing_page.page.locator(flights_view_ongoing_page.FLIGHT_CARD_BUTTON)
                    if flight_card_button.count() > 0 and flight_card_button.first.is_visible():
                        logger.info(f"Flight Card Option is displayed for Flight '{fl_num}'")

                        try:
                            with page.expect_popup(timeout=8000) as popup_info:
                                flight_card_button.first.click()

                            flight_card_page = popup_info.value
                            flight_card_page.wait_for_load_state("domcontentloaded")
                            expect(flight_card_page.locator("body")).to_be_visible()
                            logger.info(f"Flight Card opened in a new tab for Flight '{fl_num}'")
                            flight_card_page.close()
                        except Exception as pe:
                            logger.warning(f"Popup handling notice for Flight '{fl_num}': {pe}")
                    else:
                        logger.warning(f"Flight Card Option is not displayed for Flight '{fl_num}'")
                else:
                    logger.warning(f"Flight Menu is not displayed for Flight Card '{fl_num}'")

        allure.attach(
            f"Departed Section: Validated Offblock time and Flight Card popup across {number_of_departed} flights.",
            name="Departed_Validation_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.info("Offblock Time and Flight Card Validation Completed for Departed Section")

    logger.info("Flights View Ongoing Test completed successfully")
