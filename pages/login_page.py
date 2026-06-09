from pages.base_page import BasePage

class LoginPage(BasePage):

    USERNAME = "//div[@class='form-group has-feedback']/input[@id='login']"
    PASSWORD = "//div[@class='form-group has-feedback']/input[@id='password']"
    LOGIN_BTN = "//div[@class='row']//button[@id='submit']"

    def login_user(self, username, password):
        self.send_text(self.USERNAME, username)
        self.send_text(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)