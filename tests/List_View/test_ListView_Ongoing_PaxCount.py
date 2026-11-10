
# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

from playwright.sync_api import expect
import pytest
import allure
from pages.List_View.Flights_List_View_Pax_Count_Page import PAX_Count_Page
from utils.logger import get_logger
import time

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.login
def test_pax_count(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify Passenger (PAX) count validation and segregation across Ongoing, Incoming, and Departed sections.

    Steps:
    1. Authenticate / Login to application (managed via @pytest.mark.login).
    2. Navigate to Flights List View dashboard.
    3. Iterate through Ongoing, Incoming, and Departed sections.
    4. For each flight card, validate arrival and departure flight numbers.
    5. Validate passenger arrival count, departure count, and capacity thresholds.
    6. Validate PAX segregation breakdown (Adults, Children, Infants).
    """
    logger.info("Starting PAX Count Test")

    pax_count = PAX_Count_Page(page, None)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        pax_count.navigate_to_dashboard()

    failed_flights = []
    passed_flights = []

    for section in pax_count.SECTIONS:
        section_name = section["name"]
        print(f"---------------------------------------{section_name}---------------------------------------")

        with allure.step(f"Step 2: Inspect Section - {section_name}"):
            section_tab = pax_count.page.locator(section["tab"])
            expect(section_tab).to_be_visible()
            section_tab.click()
            logger.info(f"Processing {section_name} flights")

            pax_count.flights_are_visible(section_name)

            number_of_flights = pax_count.count_of_flights()
            if number_of_flights == 0:
                logger.warning(f"No Flights Found in {section_name}")
            elif 0 < number_of_flights <= 15:
                logger.info(f"Number of Flights in {section_name} is {number_of_flights}")
            else:
                number_of_flights = 15
                logger.info(f"Number of Flights in {section_name} is {number_of_flights}")

            for i in range(number_of_flights):
                print("==============================Flight Change==============================")
                try:
                    with allure.step(f"Step 3: Validating PAX Details for Flight {i + 1} in {section_name}"):
                        ongoing_flights = pax_count.page.locator(pax_count.FLIGHTS_CARDS)
                        flights = ongoing_flights.nth(i)
                        flights.scroll_into_view_if_needed()

                        # Check Arrival Number and Departure Number
                        arrival_number, departure_number = pax_count.arrival_and_departure_number(flights)

                        # Check Arrival PAX and Departure PAX
                        arrival_pax_count, departure_pax_count, total_pax = pax_count.arrival_and_departure_pax(flights)

                        # Check Flight has both Arrival and Departure Number
                        if arrival_number != '-' and departure_number not in ['-', ""] and arrival_number != departure_number:
                            try:
                                with allure.step(f"Flight {arrival_number} - {departure_number}: Both Numbers Present"):
                                    if arrival_pax_count == '-':
                                        raise Exception(f"Arrival PAX is Missing for Flight {arrival_number} - {departure_number}")
                                    arrival_pax = int(arrival_pax_count)
                                    if arrival_pax >= 185:
                                        raise Exception(f"Arrival PAX exceeded limit: {arrival_pax}")

                                    if departure_pax_count == '-':
                                        raise Exception(f"Departure PAX is Missing for Flight {arrival_number} - {departure_number}")
                                    departure_pax = int(departure_pax_count)
                                    if departure_pax >= 185:
                                        raise Exception(f"Departure PAX exceeded limit: {departure_pax}")

                                    logger.info(f"Arrival and Departure PAX are Valid for Flight {arrival_number} - {departure_number}")
                                    passed_flights.append(f"{arrival_number} - {departure_number} Passed")

                            except Exception as e:
                                pax_count.capture_failure_screenshot(
                                    locator=total_pax,
                                    flight_name="Arrival_Departure_PAX",
                                    error_message=str(e),
                                )
                                raise

                        elif arrival_number != '-' and departure_number in ['-', ""]:
                            try:
                                with allure.step(f"Flight {arrival_number}: Only Arrival Number Displayed"):
                                    if arrival_pax_count == '-':
                                        raise Exception(f"Arrival PAX is Missing for Flight {arrival_number}")
                                    arrival_pax = int(arrival_pax_count)
                                    if arrival_pax >= 185:
                                        raise Exception(f"Arrival PAX exceeded limit: {arrival_pax}")

                                    logger.info("Arrival PAX Count is Valid")
                                    passed_flights.append(f"{arrival_number} - {departure_number} Passed")

                            except Exception as e:
                                pax_count.capture_failure_screenshot(
                                    locator=total_pax,
                                    flight_name="Arrival_Departure_PAX",
                                    error_message=str(e),
                                )
                                raise

                        elif arrival_number == departure_number:
                            try:
                                with allure.step(f"Flight {arrival_number}: Same Arrival and Departure Number"):
                                    if departure_pax_count == '-':
                                        raise Exception(f"Departure PAX is Missing for Flight {arrival_number}")
                                    departure_pax = int(departure_pax_count)
                                    if departure_pax >= 185:
                                        raise Exception(f"Departure PAX exceeded limit: {departure_pax}")

                                    logger.info("Departure PAX Count is Valid")
                                    passed_flights.append(f"{arrival_number} - {departure_number} Passed")

                            except Exception as e:
                                pax_count.capture_failure_screenshot(
                                    locator=total_pax,
                                    flight_name="Arrival_Departure_PAX",
                                    error_message=str(e),
                                )
                                raise

                        logger.info(f"Validating PAX segregation for Flight {arrival_number} - {departure_number}")
                        pax_count.check_segregartion_of_pax(flights, arrival_pax_count, departure_pax_count)

                except Exception as e:
                    with allure.step(f"{arrival_number} - {departure_number} Failed"):
                        logger.error(str(e))
                    failed_flights.append(f"{arrival_number} - {departure_number} Failed: {str(e)}")

    logger.info("Testing is Done, Data Validated Successfully")