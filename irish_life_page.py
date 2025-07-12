import re
from time import sleep

from playwright.sync_api import Page, expect


class IrishLifePage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://www.irishlife.ie/investments/key-information-documents/"
        self.title = "Investment Key Information Documents | Irish Life"
        self.cookies = "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
        self.dropdown_locator = '.MuiSelect-select[role="button"]'

    def goto_website(self):
        self.page.goto(self.url)

    def assert_page_title(self):
        expect(self.page).to_have_title(re.compile(self.title))

    def accept_cookies(self):
        self.page.locator(self.cookies).click()

    # What type of product is it?
    def dropdown_product_type(self, option_text: str):
        self.select_mui_dropdown_by_class(option_text, 0)

    def dropdown_product_name(self, option_text: str):
        self.select_mui_dropdown_by_class(option_text, 1)

    def dropdown_advisor(self, option_text: str):
        self.select_mui_dropdown_by_class(option_text, 2)

    def select_mui_dropdown_by_class(self, option_text: str, index: int):
        dropdown_locator = self.page.locator(self.dropdown_locator).nth(index)
        sleep(3)  # todo add a smart dynamic wait
        dropdown_locator.click()
        option_locator = self.page.get_by_role("option", name=option_text)
        option_locator.click()

    def get_nth_pdf_button(self, index_to_click: int):
        view_pdf_buttons_locator = self.page.get_by_role("button", name="View PDF")
        all_buttons = view_pdf_buttons_locator.all()
        num_buttons = len(all_buttons)
        print("number of buttons: " + str(num_buttons))
        button_to_click = all_buttons[index_to_click]
        expect(button_to_click).to_be_visible()
        return button_to_click

    def click_all_pdf_button(self):
        view_pdf_buttons_locator = self.page.get_by_role("button", name="View PDF")
        all_buttons = view_pdf_buttons_locator.all()
        for button in all_buttons:
            button.click()

    def log_requests_after_click(self, wait_time_after_click_ms: int = 5000):
        captured_requests = []

        def request_handler(request):
            captured_requests.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "headers": request.headers
            })

        self.page.on("request", request_handler)

        try:
            self.click_all_pdf_button()  # click all buttons

            print("Capturing requests for " + str(wait_time_after_click_ms))
            self.page.wait_for_timeout(wait_time_after_click_ms)

            # 4. Log all captured requests
            print(f"\n--- All Requests Captured After Click ({len(captured_requests)} total) ---")
            if not captured_requests:
                print("No new requests were captured in the specified time after the click.")
            else:
                for i, req in enumerate(captured_requests):
                    if str(req['url']).startswith("https://apps.irishlife.ie/myonlineservices/KidQueryApi"):
                        print(str(req['url']))

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.page.remove_listener("request", request_handler)
            print("\n--- Request logging finished ---")
