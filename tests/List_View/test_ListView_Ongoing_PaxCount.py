# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-24

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
    ==============  TEST OVERVIEW ================
    Test Scenario: Verify passenger (PAX) counts, capacity limits, and passenger breakdown across Ongoing, Incoming, and Departed sections.

    Steps:
    1. Prerequisite: Sign into application using common login method.
    2. Step 1: Navigate to Flights List View dashboard.
    3. Step 2: Iterate through Ongoing, Incoming, and Departed sections:
       a. Switch to the section tab and check visible flights.
       b. Extract arrival and departure flight numbers.
       c. Check arrival passenger count, departure passenger count, and capacity limit (< 185).
       d. Check passenger breakdown (Adults, Children, Infants).
    4. Step 3: Verify overall summary of passed flights.
    """
    logger.info("Starting PAX Count Test")

    # Prerequisite: Sign into application using common login method
    with allure.step("Prerequisite: Sign into application using common login method"):
        login_to_application(page)

    pax_count = PAX_Count_Page(page, None)

    # -------------------------------------------------------------------------
    # Step 1: Open the Flights List View screen
    # -------------------------------------------------------------------------
    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        with allure.step("1.1: Open main navigation menu and click 'Flights' option"):
            pax_count.navigate_to_dashboard()
        allure.attach(
            "Successfully opened Flights List View dashboard.",
            name="Navigation_Status",
            attachment_type=allure.attachment_type.TEXT,
        )

    failed_flights = []
    passed_flights = []

    # -------------------------------------------------------------------------
    # Step 2: Iterate through sections (Ongoing, Incoming, Departed)
    # -------------------------------------------------------------------------
    for section in pax_count.SECTIONS:
        section_name = section["name"]
        logger.info(f"-------------------- Inspecting Section: {section_name} --------------------")

        with allure.step(f"Section '{section_name}': Passenger Count & Breakdown Verification"):
            with allure.step(f"2.1: Switch to '{section_name}' tab and verify flight cards"):
                section_tab = pax_count.page.locator(section["tab"])
                expect(section_tab).to_be_visible()
                section_tab.click()
                logger.info(f"Processing {section_name} flights")
                pax_count.flights_are_visible(section_name)

            total_found = pax_count.count_of_flights()
            number_of_flights = min(total_found, 15) if total_found > 0 else 0
            logger.info(f"Number of Flights to validate in {section_name}: {number_of_flights}")

            allure.attach(
                f"Section: {section_name}\nTotal Available Flights: {total_found}\nInspecting Flights: {number_of_flights}",
                name=f"{section_name}_Overview",
                attachment_type=allure.attachment_type.TEXT,
            )

            for i in range(number_of_flights):
                try:
                    flights = pax_count.page.locator(pax_count.FLIGHTS_CARDS).nth(i)
                    flights.scroll_into_view_if_needed()
                    arrival_number, departure_number = pax_count.get_arrival_and_departure_flight_numbers(flights)
                    flight_label = pax_count.get_flight_number(flights) or f"Flight {i + 1}"

                    with allure.step(f"Flight '{flight_label}': Validate Passenger Details in {section_name}"):
                        with allure.step(f"Extract PAX counts -> Arr: '{arrival_number}', Dep: '{departure_number}'"):
                            arrival_pax_count, departure_pax_count, total_pax = pax_count.arrival_and_departure_pax(flights)

                        # Determine which PAX counts to validate based on arrival/departure presence
                        check_arrival = bool(arrival_number and arrival_number != '-')
                        check_departure = bool(departure_number and departure_number != '-' and departure_number != arrival_number)
                        if arrival_number and departure_number and arrival_number == departure_number:
                            check_arrival = False
                            check_departure = True

                        # Unified PAX count and threshold validation
                        with allure.step(f"Verify passenger counts within capacity threshold (< 185)"):
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
                        with allure.step(f"Check passenger breakdown (J, Y, Infants) for Flight"):
                            logger.info(f"Validating PAX segregation for Flight '{flight_label}'")
                            pax_count.check_segregartion_of_pax(flights, arrival_pax_count, departure_pax_count)

                        allure.attach(
                            f"Flight: {flight_label}\n"
                            f"Section: {section_name}\n"
                            f"Arrival PAX: {arrival_pax_count}\n"
                            f"Departure PAX: {departure_pax_count}\n"
                            f"Total PAX: {total_pax}\n"
                            f"Validation: Capacity check (<185) and passenger breakdown passed.",
                            name=f"{flight_label}_PAX_Summary",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                except Exception as e:
                    pax_count.attach_screenshot(f"pax_failure_{section_name}_flight_{i+1}")
                    with allure.step(f"Flight '{flight_label}' Failed: {e}"):
                        logger.error(f"Flight '{flight_label}' validation failed: {e}")
                    failed_flights.append(f"{flight_label} Failed: {e}")

    # -------------------------------------------------------------------------
    # Step 3: Overall Verification Summary
    # -------------------------------------------------------------------------
    with allure.step("Step 3: Verify Overall Passenger Count Results Across All Sections"):
        allure.attach(
            f"Total Inspected Flights Passed: {len(passed_flights)}\n"
            f"Total Flights Failed: {len(failed_flights)}\n"
            f"Status: Passenger count and breakdown checks completed.",
            name="Overall_PAX_Validation_Summary",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert len(failed_flights) == 0, f"Passenger count validation failed for {len(failed_flights)} flights: {failed_flights}"

    logger.info(f"Testing Completed. Passed: {len(passed_flights)}, Failed: {len(failed_flights)}")
