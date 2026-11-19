# Author : Gowthami Ankem
# Created Date : 2026-11-06
# Modified By : Gowthami Ankem
# Modified Date : 2026-11-09
import pytest
import allure

from pages.List_View.Listview_DepartedSection_Detailedview_ActivityStatus import (
    Listview_DepartedSection_Detailedview_ActivityStatus
)
from utils.logger import get_logger

logger = get_logger(__name__)

@pytest.mark.smoke
def test_Listview_DepartedSection_Detailedview_ActivityStatus(page):

    logger.info(
        "Starting Departed Flight Detailed View Activity Status Test"
    )

    activity_status_page = (
        Listview_DepartedSection_Detailedview_ActivityStatus(page)
    )

    with allure.step("Navigate to Flights"):
        activity_status_page.navigate_to_list_view_page()

    with allure.step("Select Departed Flights"):
        activity_status_page.select_departed_flights()

    with allure.step("Open first departed flight details"):
        activity_status_page.open_first_flight_details()

    with allure.step("Validate activity statuses"):
        try:
            activity_status_page.validate_activities_status_in_chart_card()
        finally:
            activity_status_page.go_back()

    logger.info(
        "Departed Flight Detailed View Activity Status Test "
        "completed successfully"
    )
