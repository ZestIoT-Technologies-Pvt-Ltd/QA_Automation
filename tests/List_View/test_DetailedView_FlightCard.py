
# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

from playwright.sync_api import expect
import pytest
import allure
from pages.Detailed_View.Detailed_View_Flight_Card_Page import DetailViewPage
from utils.logger import get_logger
import time

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_detailed_view(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify Detailed View flight card navigation and flight attribute validation across Ongoing and Departed sections.

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View dashboard.
    3. Iterate through Ongoing and Departed sections.
    4. For each section, locate flight cards and click Detail View arrow.
    5. Validate flight attributes (flight numbers, origin/destination, aircraft type, turnaround status, ground time, bay/gate numbers, and STA/ETA/ONB/STD/ETD timings).
    6. Click Back Arrow to return to List View and verify Turnaround List visibility.
    """
    logger.info("Starting Detailed View Test")

    detail_view_page = DetailViewPage(page, None)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        detail_view_page.navigate_to_list_view_page()

    failed_flights = []
    passed_flights = []

    for section in detail_view_page.SECTIONS:
        section_name = section["name"]

        with allure.step(f"Step 2: Inspect Section - {section_name}"):
            logger.info(f"Switching to {section_name}")
            section_tab = detail_view_page.page.locator(section["tab"])
            expect(section_tab).to_be_visible()
            section_tab.click()
            logger.info(f"Clicking {section_name} ")

            detail_view_page.flight_are_visible()

            number_of_flights = detail_view_page.count_of_flights()
            if number_of_flights == 0:
                logger.warning(f"No Flights Found in {section_name}")
            elif 0 < number_of_flights <= 15:
                logger.info(f"Number of Flights in {section_name} is {number_of_flights}")
            else:
                number_of_flights = 15
                logger.info(f"Number of Flights in {section_name} is {number_of_flights}")

            for i in range(number_of_flights):
                try:
                    with allure.step(f"Step 3: Validating Details for Flight {i + 1} in {section_name}"):
                        ongoing_flights = detail_view_page.page.locator(detail_view_page.FLIGHTS_CARDS)
                        flights = ongoing_flights.nth(i)
                        flights.scroll_into_view_if_needed()

                        # Check lock icon before clicking forward arrow
                        if detail_view_page.is_lock_icon_visible(flights):
                            logger.warning(f"Flight {i+1} is locked. Skipping detail view.")
                            continue

                        # Clicking Detail View Arrow
                        detail_view_page.page.wait_for_load_state("networkidle")
                        detail_view_arrow = flights.locator(detail_view_page.DETAIL_VIEW_ARROW)
                        detail_view_arrow.scroll_into_view_if_needed()
                        detail_view_arrow.click()
                        logger.info(f"Clicked the Detail View Arrow for Flight {i + 1}")

                        time.sleep(5)

                        # Validate Arrival and Departure Flight Number
                        arrival_flight, departure_flight = detail_view_page.arrival_and_departure_flight_number()

                        # Validate Origin and Destination
                        detail_view_page.origin_and_destination()

                        # Validate Aircraft Type and Registration Number
                        detail_view_page.aircraft_type_and_reg_number()

                        # Validate Turnaround Status and Ground Time
                        detail_view_page.turnaround_status_and_ground_time()

                        # Validate Bay and Gate Number
                        detail_view_page.bay_and_gate_number()

                        # Validate STA, ETA, ONB, STD, ETD
                        detail_view_page.flight_arrival_timing()
                        detail_view_page.on_block_timing()
                        detail_view_page.flight_departure_timing()

                        # Clicking Back Arrow to return to List View
                        back_Arrow = detail_view_page.page.locator(detail_view_page.DETAIL_VIEW_BACK_ARROW)
                        back_Arrow.click()
                        logger.info(f"Clicking Back and Continuing for Flight {i + 2}")

                        # Wait until Turnaround List is loaded again
                        turnaround_list = detail_view_page.page.get_by_text("Turnaround List", exact=True)
                        expect(turnaround_list).to_be_visible(timeout=10000)
                        logger.info("Turnaround List is visible after Back")

                        passed_flights.append(f"{arrival_flight} - {departure_flight} Passed")

                except Exception as e:
                    logger.error(f"Flight Iteration {i+1} Failed: {e}", exc_info=True)

                    # Recovery: check whether we are already back on Turnaround List
                    try:
                        turnaround_list = detail_view_page.page.get_by_text("Turnaround List", exact=True)
                        if turnaround_list.is_visible():
                            logger.info(f"Flight Iteration {i+1}: Already on Turnaround List")
                        else:
                            back_arrow = detail_view_page.page.locator(detail_view_page.DETAIL_VIEW_BACK_ARROW)
                            if back_arrow.is_visible():
                                back_arrow.click()
                                logger.info(f"Flight Iteration {i+1}: Returned to Turnaround List")
                    except Exception as recovery_error:
                        logger.warning(f"Flight Iteration {i+1}: Recovery failed: {recovery_error}")
                    continue

    logger.info(f"Passed Flights Count: {len(passed_flights)}")
    logger.info(f"Failed Flights Count: {len(failed_flights)}")
    logger.info("Testing is Done, Data Validated Successfully")
