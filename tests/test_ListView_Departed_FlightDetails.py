# Author : Gowthami Ankem
# Created Date : 2026-11-26

"""
==============  INTRODUCTION ================
Test Module: test_ListView_Departed_FlightDetails
Description: Test script to validate Flight Details,  Timings,
             and AODB (Airport Operational Database) Updates in the Departed tab of Flights List View.
             - Validates Flight Details (Flight Numbers, Aircraft Type, Route, Status Badge, Bay, Gate).
             - Validates  Timings (Arrival schedule, STA, ETA, ONBL, Departure schedule, STD, ETD, OFBL, POBT, TOBT/COBT).
             - Validates AODB Data (clicks info icon under AODB column, verifies 'AODB UPDATES' dialog records in Arrival & Departure tabs, and safely closes).
"""

import pytest
import allure
from pages.List_View.ListView_Departed_FlightDetails_Page import (
    ListView_Departed_FlightDetails_Page
)
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_Departed_FlightDetails(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation of Departed Flight Details, Column Timings, and AODB Data.

    Steps:
    1. Authenticate / Login to application (managed via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed tab.
    4. Iterate through Departed flight cards:
       a) Validate Flight Details: Flight Numbers (ARR-DEP), Aircraft Type, Route, Status Badge, Bay, and Gate.
       b) Validate Column Timings: Hover on Arrival/Departure schedules to check STA, ETA, ONBL, STD, ETD, OFBL, POBT, and TOBT/COBT.
       c) Validate AODB Data: Click AODB icon ('mat-icon.infoicon'), inspect 'AODB UPDATES' dialog records in Arrival and Departure tabs, and close popup safely.
    """
    logger.info("Starting Departed Flight Details, Column Timings, and AODB Validation Test")

    flight_details_page = ListView_Departed_FlightDetails_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        flight_details_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Tab"):
        flight_details_page.select_departed_flights()

    with allure.step("Step 3: Validate Flight Details, Column Timings, and AODB Data for Departed Flights"):
        flight_results = flight_details_page.validate_departed_flight_details()

    with allure.step("Step 4: Assert Departed Flight Details, Timings, and AODB Updates"):
        if not flight_results:
            logger.info("No departed flights found to assert. Tab may be empty.")
            return

        logger.info(f"Asserting verified data for {len(flight_results)} departed flights")
        for flight in flight_results:
            idx = flight["index"]
            details = flight["details"]
            timings = flight["timings"]
            aodb = flight["aodb"]

            # 1. Assert Flight Details
            assert details["flight_numbers"] != "N/A", f"Card {idx}: Flight numbers should be visible"
            assert details["aircraft_type"] != "N/A", f"Card {idx}: Aircraft type should be visible"
            assert details["route"] != "N/A", f"Card {idx}: Route should be visible"
            assert details["status"] != "N/A", f"Card {idx}: Status badge should be visible"
            assert details["bay"] != "N/A", f"Card {idx}: Bay / Stand should be visible"

            # 2. Assert  Timings
            assert "arrival_card_display" in timings, f"Card {idx}: Arrival timings column missing"
            assert "departure_card_display" in timings, f"Card {idx}: Departure timings column missing"

            # 3. Assert AODB Updates Data
            if aodb.get("has_aodb"):
                assert aodb.get("arrival_count", 0) > 0, (
                    f"Card {idx}: Expected AODB Arrival records, but count is 0"
                )
                assert aodb.get("departure_count", 0) > 0, (
                    f"Card {idx}: Expected AODB Departure records, but count is 0"
                )

                # Validate latest Arrival record
                latest_arr = aodb["arrival_records"][0]
                assert latest_arr["flight_no"] != "", f"Card {idx}: AODB Arrival record Flight NO is empty"
                assert latest_arr["flight_status"] != "", f"Card {idx}: AODB Arrival record Flight Status is empty"
                assert latest_arr["last_update"] != "", f"Card {idx}: AODB Arrival record Last Update is empty"

                # Validate latest Departure record
                latest_dep = aodb["departure_records"][0]
                assert latest_dep["flight_no"] != "", f"Card {idx}: AODB Departure record Flight NO is empty"
                assert latest_dep["flight_status"] != "", f"Card {idx}: AODB Departure record Flight Status is empty"
                assert latest_dep["last_update"] != "", f"Card {idx}: AODB Departure record Last Update is empty"

                logger.info(
                    f"Card {idx}: Verified AODB Updates -> "
                    f"Arrival: {latest_arr['flight_no']} ({latest_arr['flight_status']}, Bay {latest_arr['bay']}), "
                    f"Departure: {latest_dep['flight_no']} ({latest_dep['flight_status']}, Bay {latest_dep['bay']})"
                )
            else:
                logger.info(f"Card {idx}: No AODB integration icon present on this card.")

    logger.info("Departed Flight Details and AODB Validation Test completed successfully")
