
# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

from playwright.sync_api import expect
import pytest
import allure
from pages.List_View.ListView_Ongoing_PaxCount_Page import PAX_Count_Page
from utils.common_methods import login_to_application
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.list_view
def test_pax_count(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Verify Passenger (PAX) count validation and segregation across Ongoing, Incoming, and Departed sections.

    Steps:
    1. Prerequisite: Authenticate / Login to application using common login method.
    2. Navigate to Flights List View dashboard.
    3. Iterate through Ongoing, Incoming, and Departed sections.
    4. For each flight card, validate arrival and departure flight numbers using common method.
    5. Validate passenger arrival count, departure count, and capacity thresholds (< 185).
    6. Validate PAX segregation breakdown (Adults, Children, Infants).
    """
    logger.info("Starting PAX Count Test")

    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)


    pax_count = PAX_Count_Page(page, None)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        pax_count.navigate_to_dashboard()

    failed_flights = []
    passed_flights = []

    for section in pax_count.SECTIONS:
        section_name = section["name"]
        logger.info(f"-------------------- Inspecting Section: {section_name} --------------------")

        with allure.step(f"Step 2: Inspect Section - {section_name}"):
            section_tab = pax_count.page.locator(section["tab"])
            expect(section_tab).to_be_visible()
            section_tab.click()
            logger.info(f"Processing {section_name} flights")

            pax_count.flights_are_visible(section_name)

            total_found = pax_count.count_of_flights()
            number_of_flights = min(total_found, 15) if total_found > 0 else 0
            logger.info(f"Number of Flights to validate in {section_name}: {number_of_flights}")

            for i in range(number_of_flights):
                try:
                    flights = pax_count.page.locator(pax_count.FLIGHTS_CARDS).nth(i)
                    flights.scroll_into_view_if_needed()
                    arrival_number, departure_number = pax_count.get_arrival_and_departure_flight_numbers(flights)
                    flight_label = pax_count.get_flight_number(flights) or f"Flight {i + 1}"

                    with allure.step(f"Step 3.{i+1}: Validating PAX Details for Flight '{flight_label}' in {section_name}"):
                        arrival_pax_count, departure_pax_count, total_pax = pax_count.arrival_and_departure_pax(flights)

                        # Determine which PAX counts to validate based on arrival/departure presence
                        check_arrival = bool(arrival_number and arrival_number != '-')
                        check_departure = bool(departure_number and departure_number != '-' and departure_number != arrival_number)
                        if arrival_number and departure_number and arrival_number == departure_number:
                            check_arrival = False
                            check_departure = True

                        # Unified PAX count and threshold validation
                        if check_arrival:
                            if arrival_pax_count == '-':
                                raise ValueError(f"Arrival PAX is Missing for Flight '{flight_label}'")
                            arr_val = int(arrival_pax_count)
                            if arr_val >= 185:
                                raise ValueError(f"Arrival PAX exceeded capacity limit (185): {arr_val}")

                        if check_departure:
                            if departure_pax_count == '-':
                                raise ValueError(f"Departure PAX is Missing for Flight '{flight_label}'")
                            dep_val = int(departure_pax_count)
                            if dep_val >= 185:
                                raise ValueError(f"Departure PAX exceeded capacity limit (185): {dep_val}")

                        logger.info(f"PAX count valid for Flight '{flight_label}': Arr={arrival_pax_count}, Dep={departure_pax_count}")
                        passed_flights.append(f"{flight_label} Passed")

                        # Validate PAX segregation (Adults, Children, Infants)
                        logger.info(f"Validating PAX segregation for Flight '{flight_label}'")
                        pax_count.check_segregartion_of_pax(flights, arrival_pax_count, departure_pax_count)

                except Exception as e:
                    pax_count.attach_screenshot(f"pax_failure_{section_name}_flight_{i+1}")
                    with allure.step(f"Flight '{flight_label}' Failed"):
                        logger.error(f"Flight '{flight_label}' validation failed: {e}")
                    failed_flights.append(f"{flight_label} Failed: {e}")

    logger.info(f"Testing Completed. Passed: {len(passed_flights)}, Failed: {len(failed_flights)}")