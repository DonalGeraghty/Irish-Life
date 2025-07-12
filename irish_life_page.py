import os
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
        print(f"Attempting to click MUI dropdown by class...")
        dropdown_locator = self.page.locator(self.dropdown_locator).nth(index)
        sleep(3)  # add a smart wait
        dropdown_locator.click()
        option_locator = self.page.get_by_role("option", name=option_text)
        option_locator.click()
        print(f"Selected option: '{option_text}'.")

    def get_pdf_button(self, index_to_click: int):
        print("\n--- Interacting with 'View PDF' Buttons ---")
        view_pdf_buttons_locator = self.page.get_by_role("button", name="View PDF")
        all_buttons = view_pdf_buttons_locator.all()

        num_buttons = len(all_buttons)
        print(f"Found {num_buttons} 'View PDF' buttons on the page.")

        # 3. Click the Nth one
        if num_buttons == 0:
            print("No 'View PDF' buttons found to click.")
            raise ValueError("No 'View PDF' buttons found on the page.")
        elif index_to_click >= num_buttons or index_to_click < 0:
            print(f"Error: Index {index_to_click} is out of bounds. Only {num_buttons} buttons found.")
            raise IndexError(f"Button index {index_to_click} out of range (0-{num_buttons - 1})")
        else:
            button_to_click = all_buttons[index_to_click]
            print(f"Clicking the button at index {index_to_click}...")

            # It's good practice to ensure the button is visible before clicking,
            # though Playwright's click() usually handles this.
            expect(button_to_click).to_be_visible()
            # button_to_click.click()
            print(f"Successfully clicked button at index {index_to_click}.")
            return button_to_click

    def log_requests_after_click(self, wait_time_after_click_ms: int = 5000):
        """
        Logs all network requests that occur after clicking a specified button.

        Args:
            page: The Playwright Page object.
            button_locator: A Playwright Locator for the button to click.
            wait_time_after_click_ms: How long (in milliseconds) to wait and collect requests
                                      after the button click. Adjust based on page load time.
        """
        print(f"\n--- Logging Requests after Clicking Button ---")

        captured_requests = []

        # Define the handler function for requests
        def request_handler(request):
            captured_requests.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "headers": request.headers  # Optional: capture headers
                # You can add more request properties here if needed
            })
            print(f"Captured Request: {request.method} {request.url} ({request.resource_type})") # Optional: log as they come in

        # 1. Set up the request listener BEFORE clicking the button
        self.page.on("request", request_handler)

        try:
            # 2. Click the button
            print("Clicking the button")
            #button_locator.click()
            self.get_pdf_button(5).click()

            # 3. Wait for requests to finish loading
            # This is a crucial step. Adjust the time based on how long
            # your page typically takes to load new content after the click.
            # page.wait_for_load_state('networkidle') might be too aggressive if background tasks keep running.
            # A short timeout is a simple way, or wait for a specific element to appear.
            print(f"Waiting for {wait_time_after_click_ms}ms to capture requests...")
            self.page.wait_for_timeout(wait_time_after_click_ms)

            # 4. Log all captured requests
            print(f"\n--- All Requests Captured After Click ({len(captured_requests)} total) ---")
            if not captured_requests:
                print("No new requests were captured in the specified time after the click.")
            else:
                for i, req in enumerate(captured_requests):
                    print(f"[{i + 1}] {req['method']} {req['url']} ({req['resource_type']})")
                    # if req['headers']: # Uncomment to log headers
                    #     print(f"    Headers: {req['headers']}")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # 5. IMPORTANT: Remove the listener to prevent it from affecting subsequent actions/tests
            self.page.remove_listener("request", request_handler)
            print("\n--- Request logging finished ---")
