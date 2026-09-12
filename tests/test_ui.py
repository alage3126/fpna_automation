# tests/test_ui.py
import allure
import pytest
from playwright.sync_api import Page, expect

@allure.epic("FP&A Web Dashboard")
@allure.feature("Authentication & Executive Summary")
@allure.title("Verify end-to-end user login workflow and secure dashboard entry")
@allure.severity(allure.severity_level.BLOCKER)
def test_user_login_flow(page: Page):
    with allure.step("Navigate to application login page"):
        page.goto("https://the-internet.herokuapp.com/login")
    
    with allure.step("Fill credentials and submit login form"):
        page.fill("input[name='username']", "tomsmith")
        page.fill("input[name='password']", "SuperSecretPassword!")
        page.click("button[type='submit']")
    
    with allure.step("Capture post-login dashboard view"):
        screenshot_bytes = page.screenshot(full_page=True)
        allure.attach(
            screenshot_bytes,
            name="Secure Dashboard After Login",
            attachment_type=allure.attachment_type.PNG
        )
    
    with allure.step("Verify successful authentication banner and private area access"):
        success_banner = page.locator("#flash")
        expect(success_banner).to_be_visible()
        expect(success_banner).to_contain_text("You logged into a secure area!")
        expect(page).to_have_url("https://the-internet.herokuapp.com/secure")