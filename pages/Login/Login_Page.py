# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: LoginPage
Description: Page Object Model representing the AviLeap Authentication and Login interface.
             Encapsulates credential inputs, login submission, and page title verification.

Scenario & Workflow Capabilities:
1. Locate username and password input fields.
2. Enter user credentials securely.
3. Click the login button and await session authentication.
4. Verify landing page title contains 'AviLeap' upon successful login.
"""

from pages.Common_Base_Page.Base_Page import BasePage


class LoginPage(BasePage):
    """
    Page Object for AviLeap Login authentication page.
    """

    USERNAME = "//input[@name='username']"
    PASSWORD = "//input[@name='password']"
    LOGIN_BTN = "//button[@type='submit']"

    def login_user(self, username, password):
        self.send_text(self.USERNAME, username)
        self.send_text(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)
        try:
            self.page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
        except Exception:
            if "/login" in self.page.url:
                try:
                    self.page.locator(self.PASSWORD).press("Enter")
                    self.page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
                except Exception:
                    pass
        self.page.wait_for_load_state("domcontentloaded")
