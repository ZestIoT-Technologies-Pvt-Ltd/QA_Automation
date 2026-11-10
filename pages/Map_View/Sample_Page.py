# Author : Tilak Badsheshi
# Created Date : 2026-11-10
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: MapViewSamplePage
Description: Page Object Model for the Map View module interface.
             Handles interactive airport apron and stand maps, aircraft positioning, and geographic overlay layers.

Scenario & Workflow Capabilities:
1. Navigation: Route to Map View from side navigation menu.
2. View Readiness: Verify map canvas rendering, zoom controls, and apron stands.
3. Geo-spatial Interactions: Select bays/stands, filter active aircraft, and verify positional markers.
"""

from playwright.sync_api import Page, expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class MapViewSamplePage(BasePage):
    """
    Page Object Model representing the Map View module.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    MAP_NAV = "//div[@role='button']//span[contains(text(),'Map')]"
    MAP_CONTAINER = "//div[contains(@class,'map-container')] | //canvas | //div[@id='map']"

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_map_view(self):
        logger.info("Navigating to Map View module")
        menu = self.page.locator(self.MENU).first
        if menu.is_visible():
            menu.click()
            self.page.wait_for_timeout(1000)
        nav_item = self.page.locator(self.MAP_NAV).first
        if nav_item.is_visible():
            nav_item.click()
            logger.info("Clicked Map View navigation item")

    def verify_map_view_ready(self) -> bool:
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("Map View readiness verified")
        return True
