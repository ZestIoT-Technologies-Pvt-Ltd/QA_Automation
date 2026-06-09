import allure
from utils import logger


class BasePage:

    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def open_application(self):
        with allure.step("Open Application"):
            self.page.goto(self.base_url)

    # ACTIONS
    def click(self, locator):
        with allure.step(f"Click on {locator}"):
            self.page.locator(locator).click()

    def send_text(self, locator, text):
        with allure.step(f"Enter '{text}' into {locator}"):
            self.page.locator(locator).fill(text)

    def get_text(self, locator):
        return self.page.locator(locator).inner_text()

    def is_visible(self, locator):
        return self.page.locator(locator).is_visible()

    def get_title(self):
        return self.page.title()

    def capture_failure_screenshot(self, locator=None, flight_name="Unknown Flight", error_message=""):

        try:
            # Remove previous highlighted borders
            self.page.evaluate("""
                () => {
                    document.querySelectorAll('*').forEach(element => {
                        element.style.border = '';
                    });
                }
            """)
            
            # Highlight failed element
            if locator:
                locator.evaluate("""
                    element => {
                        element.style.border = '2px solid red';
                    }
                """)

            # Take Screenshot
            screenshot = self.page.screenshot(full_page=True)

            # Attach Screenshot in Allure
            allure.attach(screenshot, name=f"{flight_name} Failure Screenshot", attachment_type=allure.attachment_type.PNG)

            # Attach Error Message
            allure.attach(error_message, name=f"{flight_name} Error", attachment_type=allure.attachment_type.TEXT)

        except Exception as screenshot_error:
            logger.error(f"Unable to Capture Screenshot: {str(screenshot_error)}")