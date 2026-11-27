# Author : Gowthami Ankem
# Created Date : 2026-11-20

"""
==============  INTRODUCTION ================
Test Module: test_ListView_Departed_AccesstoAIMedia
Description: Test script to validate AI Captured Media in Departed Section of Flights List View.
             Inspects departed flights, verifies turnaround progress indicators, expands
             activity panels (Arrival, Departure, Additional), and verifies that AI-captured media
             (images/videos) can be opened and displayed in the media player popup.
"""

import pytest
import allure
from pages.List_View.ListView_Departed_AccesstoAIMedia_Page import (
    ListView_Departed_AccesstoAIMedia_Page
)
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_ListView_Departed_AccesstoAIMedia(page):
    """
    ==============  INTRODUCTION ================
    Test Scenario: Validation of AI Captured Media for Departed Flights.

    Steps:
    1. Authenticate / Login to application (managed as prerequisite via page fixture).
    2. Navigate to Flights List View dashboard.
    3. Select Departed Section tab.
    4. Iterate through Departed flights:
       a) Click flight card to open detailed operation view.
       b) Identify flight structure (Turnaround vs Split flight).
       c) Check activity progress indicators.
       d) If Split flight: Expand Arrival, Departure, and Additional activity accordion panels.
       e) For each AI media item (.image-class):
          - Click the media item to open the video/media player popup (#player).
          - Capture verification screenshot of the player.
          - Close the player popup.
       f) If Turnaround flight: Verify activity rows and open/validate AI media player.
    """
    logger.info("Starting Departed Section Access to AI Media Validation Test")

    ai_media_page = ListView_Departed_AccesstoAIMedia_Page(page)

    with allure.step("Step 1: Navigate to Flights List View Dashboard"):
        ai_media_page.navigate_to_list_view_page()

    with allure.step("Step 2: Select Departed Section"):
        ai_media_page.select_departed_flights()

    with allure.step("Step 3: Validate AI Captured Media for Departed Flights"):
        ai_media_page.validate_departed_ai_media()

    logger.info("Departed Section Access to AI Media Validation Test completed successfully")
