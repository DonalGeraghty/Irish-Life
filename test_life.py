import pytest
from playwright.sync_api import Page, sync_playwright

from irish_life_page import IrishLifePage


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # You can choose 'firefox' or 'webkit' as well
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    page = browser.new_page()
    yield page
    page.close()


def test_life(page: Page):
    life_page = IrishLifePage(page)
    life_page.goto_website()
    page.wait_for_load_state()
    life_page.assert_page_title()
    life_page.accept_cookies()

    # todo hardcoded, but make this dyanmic and click all combinations of dropdowns.
    life_page.dropdown_product_type('Regular Premium')
    life_page.dropdown_product_name('EBS Choice Saver')
    life_page.dropdown_advisor('EBS')
    life_page.log_requests_after_click()