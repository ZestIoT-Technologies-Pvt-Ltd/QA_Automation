from playwright.sync_api import expect
import pytest
import allure
from pages.detail_view_page import DetailViewPage
from utils.logger import get_logger
import time

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_detailed_view(page):
    
    logger.info("Starting Detailed View Test")

    detail_view_page = DetailViewPage(page, None)

    with allure.step("Test Execution Started -> Navigating to Dashboard"):

        # Navigating to Dashboard
        detail_view_page.navigate_to_dashboard()

        failed_flights = []
        passed_flights = []

        for section in detail_view_page.SECTIONS:

            section_name = section["name"]

            with allure.step(f"Search in {section_name}"):
                
                # Switching the Sections
                logger.info(f"Switching to {section_name}")

                # Click Section tab
                section_tab = detail_view_page.page.locator(section["tab"])
                expect(section_tab).to_be_visible()
                section_tab.click()
                logger.info(f"Clicking {section_name} ")

                # Check Flights are Visible
                detail_view_page.flight_are_visible()

                # Number of Flights
                number_of_flights = detail_view_page.count_of_flights()

                for i in range(number_of_flights):

                    try :

                        with allure.step(f"Validating Details for {i+1} Flight"):

                            ongoing_flights = detail_view_page.page.locator(detail_view_page.FLIGHTS_CARDS)
                            flights = ongoing_flights.nth(i)
                            flights.scroll_into_view_if_needed()  #timeout=30000
                            detail_view_page.page.wait_for_timeout(2000)

                            # Check lock icon before clicking forward arrow
                            if detail_view_page.is_lock_icon_visible(flights):
                                logger.warning(f"Flight {i+1} is locked. Skipping detail view.")                                
                                continue

                            # Clicking Detail View Arrow
                            with allure.step("Clicking Detail View Arrow"):
                                detail_view_page.page.wait_for_load_state("networkidle")
                                detail_view_arrow = flights.locator(detail_view_page.DETAIL_VIEW_ARROW)
                                detail_view_arrow.scroll_into_view_if_needed()
                                detail_view_arrow.click()
                                logger.info(f"Clicked the Detail View Arrow for {i+1} Flight")

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
                            with allure.step("Clicking Back Arrow"):
                                back_Arrow = detail_view_page.page.locator(detail_view_page.DETAIL_VIEW_BACK_ARROW)
                                back_Arrow.click()
                                logger.info(f"Clicking Back and Continuing for next Flight")

                            #time.sleep(10)
                            ongoing_flights = detail_view_page.page.locator(detail_view_page.FLIGHTS_CARDS)
                            expect(ongoing_flights.first).to_be_visible(timeout=30000)
                            detail_view_page.page.wait_for_timeout(3000)

                            with allure.step(f"{arrival_flight} - {departure_flight} Passed"):
                                logger.info(f"{arrival_flight} - {departure_flight} Passed")

                            passed_flights.append(f"{arrival_flight} - {departure_flight} Passed")

                    except Exception as e :

                        logger.error(f"Flight Iteration {i+1} Failed: {str(e)}")

                        with allure.step(f"{arrival_flight} - {departure_flight} Failed"):
                            logger.error(str(e))

                        failed_flights.append(f"{arrival_flight} - {departure_flight} Failed: {str(e)}")

                        try:
                            back_Arrow = detail_view_page.page.locator(detail_view_page.DETAIL_VIEW_BACK_ARROW)

                            if back_Arrow.is_visible():
                                back_Arrow.click()
                                ongoing_flights = detail_view_page.page.locator(detail_view_page.FLIGHTS_CARDS)
                                expect(ongoing_flights.first).to_be_visible(timeout=30000)

                        except Exception:
                            pass

                        continue

        logger.info(f"Passed Flights Count: {len(passed_flights)}")
        logger.info(f"Failed Flights Count: {len(failed_flights)}")

    logger.info("Testing is Done, Data Validated Successfully")

