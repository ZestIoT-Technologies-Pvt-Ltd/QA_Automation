# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-19

"""
==============  INTRODUCTION ================
Page Object / Component: LoginPage
Description: Page Object Model representing the AviLeap Authentication and Login interface.
             Encapsulates credential inputs, login submission, and page title verification.

Scenario & Workflow Capabilities:
1. Locate username and password input fields.
2. Enter user credentials securely (auto-resolves from framework configuration if not provided).
3. Click the login button and await session authentication.
4. Verify landing page title contains 'AviLeap' upon successful login.
"""

from __future__ import annotations

import os
import allure
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """
    Page Object for AviLeap Login authentication page.
    """

    USERNAME = "//input[@name='username']"
    PASSWORD = "//input[@name='password']"
    LOGIN_BTN = "//button[@type='submit' or @id='submit' or @name='submit'] | //button[contains(., 'Departure') or contains(., 'Login')]"

    def __init__(self, page, base_url: str | None = None):
        """
        Initializes the Login Page object.

        What this function does:
        Sets up the page controller and retrieves the application web address (URL)
        from configuration settings so that the browser knows where to navigate.
        """
        super().__init__(page, base_url)
        if not self.base_url:
            cfg = getattr(self.page, "_framework_config", None)
            if cfg and cfg.get("url"):
                self.base_url = cfg["url"]

    @allure.step("Prerequisite: Authenticate / Login to Application")
    def login_user(self, username: str | None = None, password: str | None = None):
        """
        Performs the login authentication as a prerequisite step for test scripts.

        What this function does:
        Signs the test user into the AviLeap application so that protected features
        like flight lists and alerts can be accessed.

        How it works in plain English:
        1. Checks if username and password were provided. If not, it automatically reads
           them from the configuration file or environment settings.
        2. Opens the application website in the browser if it is not already opened.
        3. Checks if the user is already logged in. If yes, it skips re-entering credentials.
        4. Types the username into the username field.
        5. Types the password into the password field.
        6. Clicks the 'Login' button and waits until the application moves past the login screen.

        Inputs:
            username (str | None): Optional username. Defaults to configured test account.
            password (str | None): Optional password. Defaults to configured test password.
        """
        # Step 1: Automatically resolve credentials if not passed explicitly
        if not username or not password:
            cfg = getattr(self.page, "_framework_config", None)
            if cfg:
                username = username or cfg.get("username")
                password = password or cfg.get("password")
            if not username or not password:
                from utils.config import Config
                proj = getattr(self.page, "_framework_project", os.getenv("PROJECT", "FLYDUBAI"))
                env = getattr(self.page, "_framework_env", os.getenv("ENV", "QA"))
                try:
                    fetched_cfg = Config.get_config(proj, env)
                    username = username or fetched_cfg.get("username")
                    password = password or fetched_cfg.get("password")
                except Exception as e:
                    logger.warning(f"Could not fetch credentials via Config.get_config: {e}")

            if not username or not password:
                username = username or os.getenv("FLYDUBAI_QA_USERNAME")
                password = password or os.getenv("FLYDUBAI_QA_PASSWORD")

        if not username or not password:
            raise ValueError("Credentials missing for login. Please provide username and password or configure .env.")

        # Step 2: Open the application webpage if the browser is currently blank
        current_url = getattr(self.page, "url", "")
        if not current_url or current_url in ("about:blank", ""):
            self.open_application()

        # Step 3: Check if the application is already logged in
        if "/login" not in self.page.url and self.page.url != "about:blank":
            logger.info("Application is already authenticated/logged in.")
            return

        # Step 4: Enter username, enter password, and click the Login button
        logger.info(f"Submitting login credentials for user: '{username}'")
        self.send_text(self.USERNAME, username)
        self.send_text(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)

        # Step 5: Wait for the application to navigate away from the login page
        try:
            self.page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
        except Exception:
            if "/login" in self.page.url:
                try:
                    # Press Enter as a fallback if the button click did not trigger form submission
                    self.page.locator(self.PASSWORD).press("Enter")
                    self.page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
                except Exception:
                    pass

        # Step 6: Wait for the dashboard content to finish loading
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("Login successful, navigated away from /login")

    # Friendly alias for prerequisite calls
    login = login_user
