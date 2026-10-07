<<<<<<< HEAD
from pages.base_page import BasePage

class LoginPage(BasePage):

    USERNAME = "//div[@class='form-group has-feedback']/input[@id='login']"
    PASSWORD = "//div[@class='form-group has-feedback']/input[@id='password']"
    LOGIN_BTN = "//div[@class='row']//button[@id='submit']"

    def login_user(self, username, password):
        self.send_text(self.USERNAME, username)
        self.send_text(self.PASSWORD, password)
=======
from pages.base_page import BasePage

class LoginPage(BasePage):

    USERNAME = "//input[@name='username']"
    PASSWORD = "//input[@name='password']"
    LOGIN_BTN = "//button[@type = 'submit']/span[text() = 'Log In']"

    def login_user(self, username, password):
        self.send_text(self.USERNAME, username)
        self.send_text(self.PASSWORD, password)
>>>>>>> 8d21396 (Update automation framework and test cases)
        self.click(self.LOGIN_BTN)