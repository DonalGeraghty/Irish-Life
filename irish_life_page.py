import re
import requests
import os
from time import sleep
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import Page, expect


class IrishLifePage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://www.irishlife.ie/investments/key-information-documents/"
        self.title = "Investment Key Information Documents | Irish Life"
        self.cookies = "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
        self.dropdown_locator = '.MuiSelect-select[role="button"]'
        self.dropdown_product_type_index = 0
        self.dropdown_product_name_index = 1
        self.dropdown_advisor_index = 2

    def goto_website(self):
        self.page.goto(self.url)

    def assert_page_title(self):
        expect(self.page).to_have_title(re.compile(self.title))

    def accept_cookies(self):
        self.page.locator(self.cookies).click()

    # What type of product is it?
    def dropdown_product_type(self, option_text: str):
        self.select_mui_dropdown_by_class(option_text, self.dropdown_product_type_index)

    def dropdown_product_name(self, option_text: str):
        self.select_mui_dropdown_by_class(option_text, self.dropdown_product_name_index)

    def dropdown_advisor(self, option_text: str):
        self.select_mui_dropdown_by_class(option_text, self.dropdown_advisor_index)

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

    def download_all_pdfs(self, wait_time_after_click_ms: int = 5000, download_dir: str = "downloaded_pdfs"):
        """
        Downloads all PDFs by triggering downloads through Playwright's download mechanism.
        
        Args:
            wait_time_after_click_ms: Time to wait after clicking buttons to capture responses
            download_dir: Directory to save downloaded PDFs
        """
        # Set up download handling
        self.page.set_default_timeout(30000)  # 30 second timeout
        
        # Create download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            print(f"Created download directory: {download_dir}")
        
        # Get all PDF buttons first
        view_pdf_buttons_locator = self.page.get_by_role("button", name="View PDF")
        all_buttons = view_pdf_buttons_locator.all()
        
        if not all_buttons:
            print("No PDF buttons found on the page.")
            return
        
        print(f"Found {len(all_buttons)} PDF buttons to process")
        
        # Set up download event handler
        downloads = []
        
        def download_handler(download):
            downloads.append(download)
            print(f"Download event triggered: {download.suggested_filename}")
        
        self.page.on("download", download_handler)
        
        # Process each button individually to trigger downloads
        for i, button in enumerate(all_buttons):
            try:
                print(f"\nProcessing PDF button {i+1}/{len(all_buttons)}")
                
                # Wait for button to be visible and clickable
                expect(button).to_be_visible()
                
                # Clear any previous downloads
                downloads.clear()
                
                # Click the button to trigger download
                button.click()
                
                # Wait a bit for download to start
                self.page.wait_for_timeout(2000)
                
                if downloads:
                    download = downloads[0]
                    suggested_filename = download.suggested_filename
                    print(f"Download started: {suggested_filename}")
                    
                    # Generate a better filename from the button context if possible
                    try:
                        # Try to get more context about what this PDF represents
                        # Look for nearby text or elements that might indicate the product
                        button_context = button.locator("xpath=..").text_content()
                        if button_context:
                            # Extract meaningful parts from context
                            context_parts = button_context.strip().split()
                            if context_parts:
                                context_name = "_".join(context_parts[:3])  # Take first 3 words
                                filename = f"{context_name}_{i+1}.pdf"
                            else:
                                filename = suggested_filename
                        else:
                            filename = suggested_filename
                    except:
                        filename = suggested_filename
                    
                    # Ensure filename is safe and has .pdf extension
                    filename = re.sub(r'[^\w\-_.]', '_', filename)
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    
                    # Save the file
                    filepath = os.path.join(download_dir, filename)
                    download.save_as(filepath)
                    
                    print(f"✓ Successfully downloaded: {filename}")
                else:
                    print(f"✗ No download event triggered for button {i+1}")
                
                # Small delay between downloads to avoid overwhelming the server
                self.page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"✗ Error processing button {i+1}: {e}")
                continue
        
        # Remove the download event handler
        self.page.remove_listener("download", download_handler)
        
        print(f"\n--- PDF Download Complete ---")
        print(f"Total buttons processed: {len(all_buttons)}")
        print(f"Download directory: {os.path.abspath(download_dir)}")
        
        # List downloaded files
        try:
            downloaded_files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
            print(f"Files downloaded: {len(downloaded_files)}")
            for file in downloaded_files:
                file_path = os.path.join(download_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
        except Exception as e:
            print(f"Could not list downloaded files: {e}")
