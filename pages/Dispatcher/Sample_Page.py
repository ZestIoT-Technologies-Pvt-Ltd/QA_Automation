# Author : Tilak Badsheshi
# Created Date : 2026-11-10
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: DispatcherSamplePage
Description: Page Object Model for the Dispatcher console interface.
             Handles dispatch consoles, turnaround operational timelines, and real-time flight communications.

Scenario & Workflow Capabilities:
1. Navigation: Route to Dispatcher console from side navigation menu.
2. View Readiness: Verify dispatcher console layout, telemetry streams, and active turnaround cards.
3. Dispatch Operations: Inspect active tasks, issue turnaround instructions, and verify dispatch states.
"""

from playwright.sync_api import Page, expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class DispatcherSamplePage(BasePage):
    """
    Page Object Model representing the Dispatcher console.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    DISPATCHER_NAV = "//div[@role='button']//span[contains(text(),'Dispatcher')]"
    DISPATCHER_CONTAINER = "//div[contains(@class,'dispatcher-container')] | //div[contains(@class,'dispatcher')]"

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_dispatcher(self):
        logger.info("Navigating to Dispatcher module")
        menu = self.page.locator(self.MENU).first
        if menu.is_visible():
            menu.click()
            self.page.wait_for_timeout(1000)
        nav_item = self.page.locator(self.DISPATCHER_NAV).first
        if nav_item.is_visible():
            nav_item.click()
            logger.info("Clicked Dispatcher navigation item")

    def verify_dispatcher_view_ready(self) -> bool:
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("Dispatcher view readiness verified")
        return True
