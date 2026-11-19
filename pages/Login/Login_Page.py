from pages.Common_Base_Page.Base_Page import BasePage

class LoginPage(BasePage):

    USERNAME = "//input[@name='username']"
    PASSWORD = "//input[@name='password']"
    LOGIN_BTN = (
        "//button[@id='submit'] | "
        "//button[@name='submit'] | "
        "//button[@type='submit'] | "
        "//button[contains(., 'Log In')] | "
        "//button[contains(., 'Ready for Departure')]"
    )

    def login_user(self, username, password):
        self.send_text(self.USERNAME, username)
        self.send_text(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)