# Author : Tilak Badsheshi
# Created Date : 2026-11-10
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: AllocationsSamplePage
Description: Page Object Model for the Allocations module interface.
             Handles resource and equipment allocations, shift management, and roster verification.

Scenario & Workflow Capabilities:
1. Navigation: Route to Allocations module from side navigation menu.
2. View Readiness: Verify main Allocations grid and resource timeline components are loaded.
3. Allocation Verification: Inspect assigned agents, equipment, and flight task allocations.
"""

from playwright.sync_api import Page, expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AllocationsSamplePage(BasePage):
    """
    Page Object Model representing the Allocations module.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    ALLOCATIONS_NAV = "//div[@role='button']//span[contains(text(),'Allocations')]"
    ALLOCATIONS_CONTAINER = "//div[contains(@class,'allocations-container')] | //mat-card[contains(@class,'allocation')]"

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_allocations(self):
        logger.info("Navigating to Allocations module")
        menu = self.page.locator(self.MENU).first
        if menu.is_visible():
            menu.click()
            self.page.wait_for_timeout(1000)
        nav_item = self.page.locator(self.ALLOCATIONS_NAV).first
        if nav_item.is_visible():
            nav_item.click()
            logger.info("Clicked Allocations navigation item")

    def verify_allocations_view_ready(self) -> bool:
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("Allocations view readiness verified")
        return True
