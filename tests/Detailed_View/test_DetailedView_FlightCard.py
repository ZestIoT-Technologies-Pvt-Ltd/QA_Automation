# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

from playwright.sync_api import expect
import pytest
import allure
from pages.Detailed_View.Detailed_View_Flight_Card_Page import DetailViewPage
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.detailed_view
def test_detailed_view(page):
    """
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify opening Detailed View flight card and checking all flight details across Ongoing and Departed sections.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Iterate through Ongoing and Departed sections:
       a. Switch to the section tab and check visible flights.
       b. Click the forward Detail View arrow on the flight card.
       c. Check flight numbers, route, aircraft info, ground time, bay/gate, and flight timings.
       d. Click the Back arrow to return to Turnaround List.
    4. Step 3: Verify overall summary of passed flights.
    """
    logger.info("Starting Detailed View Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    detail_view_page = DetailViewPage(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            detail_view_page.navigate_to_list_view_page()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    failed_flights = []
    passed_flights = []

    # -------------------------------------------------------------------------
    # Step 2: Iterate through sections (Ongoing, Departed)
    # -------------------------------------------------------------------------
    for section in detail_view_page.SECTIONS:
        section_name = section["name"]

        with allure.step(f"Section '{section_name}': Detailed Flight Card Verification"):
            with allure.step(f"2.1: Switch to '{section_name}' section tab and check visible flights"):
                logger.info(f"Switching to {section_name}")
                section_tab = detail_view_page.page.locator(section["tab"])
                expect(section_tab).to_be_visible()
                section_tab.click()
                logger.info(f"Clicking {section_name} ")
                detail_view_page.flight_are_visible()

            number_of_flights = detail_view_page.count_of_flights()
            if number_of_flights == 0:
                logger.warning(f"No Flights Found in {section_name}")
                allure.attach(f"Section '{section_name}' has 0 flights loaded. Skipping.", name=f"{section_name}_No_Flights", attachment_type=allure.attachment_type.TEXT)
                continue
            elif 0 < number_of_flights <= 15:
                logger.info(f"Number of Flights in {section_name} is {number_of_flights}")
            else:
                number_of_flights = 15
                logger.info(f"Number of Flights in {section_name} is {number_of_flights}")

            allure.attach(
                f"Section: {section_name}\nTotal Available Flights: {number_of_flights}",
                name=f"{section_name}_Overview",
                attachment_type=allure.attachment_type.TEXT,
            )

            for i in range(number_of_flights):
                try:
                    ongoing_flights = detail_view_page.page.locator(detail_view_page.FLIGHTS_CARDS)
                    flights = ongoing_flights.nth(i)
                    flights.scroll_into_view_if_needed()
                    flight_num = detail_view_page.get_flight_number(flights) or f"Flight {i + 1}"

                    with allure.step(f"Flight '{flight_num}': Validate Detailed Flight Attributes in {section_name}"):
                        # Check lock icon before clicking forward arrow
                        if detail_view_page.is_lock_icon_visible(flights):
                            logger.warning(f"Flight '{flight_num}' is locked. Skipping detail view.")
                            with allure.step(f"Flight '{flight_num}' is locked. Skipping detail view."):
                                pass
                            continue

                        with allure.step("Click forward arrow to open Detailed View"):
                            detail_view_page.page.wait_for_load_state("networkidle")
                            detail_view_arrow = flights.locator(detail_view_page.DETAIL_VIEW_ARROW)
                            detail_view_arrow.scroll_into_view_if_needed()
                            detail_view_arrow.click()
                            logger.info(f"Clicked the Detail View Arrow for Flight '{flight_num}'")
                            detail_view_page.wait_for_loading_to_finish()
                            detail_view_page.page.wait_for_timeout(1500)

                        with allure.step("Check flight numbers and route (Origin & Destination)"):
                            arrival_flight, departure_flight = detail_view_page.arrival_and_departure_flight_number()
                            detail_view_page.origin_and_destination()

                        with allure.step("Check aircraft type and registration number"):
                            detail_view_page.aircraft_type_and_reg_number()

                        with allure.step("Check turnaround status, ground time, and bay/gate numbers"):
                            detail_view_page.turnaround_status_and_ground_time()
                            detail_view_page.bay_and_gate_number()

                        with allure.step("Check flight arrival and departure timings (STA, ETA, ONB, STD, ETD)"):
                            detail_view_page.flight_arrival_timing()
                            detail_view_page.on_block_timing()
                            detail_view_page.flight_departure_timing()

                        with allure.step("Click Back arrow and return to Turnaround List"):
                            back_Arrow = detail_view_page.page.locator(detail_view_page.DETAIL_VIEW_BACK_ARROW)
                            back_Arrow.click()
                            logger.info(f"Clicking Back and Continuing for Flight {i + 2}")
                            turnaround_list = detail_view_page.page.get_by_text("Turnaround List", exact=True)
                            expect(turnaround_list).to_be_visible(timeout=10000)
                            logger.info("Turnaround List is visible after Back")

                        passed_flights.append(f"{arrival_flight} - {departure_flight} Passed")

                        allure.attach(
                            f"Flight: {flight_num}\n"
                            f"Arrival: {arrival_flight} | Departure: {departure_flight}\n"
                            f"Section: {section_name}\n"
                            f"Status: Detailed attributes (aircraft, route, bay/gate, timings) verified successfully.",
                            name=f"{flight_num}_Details_Summary",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                except Exception as e:
                    logger.error(f"Flight '{flight_num}' Failed: {e}", exc_info=True)
                    failed_flights.append(f"{flight_num} Failed: {e}")

                    # Recovery: check whether we are already back on Turnaround List
                    try:
                        turnaround_list = detail_view_page.page.get_by_text("Turnaround List", exact=True)
                        if turnaround_list.is_visible():
                            logger.info(f"Flight '{flight_num}': Already on Turnaround List")
                        else:
                            back_arrow = detail_view_page.page.locator(detail_view_page.DETAIL_VIEW_BACK_ARROW)
                            if back_arrow.is_visible():
                                back_arrow.click()
                                logger.info(f"Flight '{flight_num}': Returned to Turnaround List")
                    except Exception as recovery_error:
                        logger.warning(f"Flight '{flight_num}': Recovery failed: {recovery_error}")
                    continue

    # -------------------------------------------------------------------------
    # Step 3: Overall Verification Summary
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Verify Overall Detailed View Results Summary"):
        allure.attach(
            f"Total Flights Checked & Passed: {len(passed_flights)}\n"
            f"Total Flights Failed: {len(failed_flights)}\n"
            f"Status: Detailed flight card attributes verification completed.",
            name="Overall_DetailedView_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert len(failed_flights) == 0, f"Detailed View validation failed for {len(failed_flights)} flights: {failed_flights}"

    logger.info(f"Passed Flights Count: {len(passed_flights)}")
    logger.info(f"Failed Flights Count: {len(failed_flights)}")
    logger.info("Testing is Done, Data Validated Successfully")
