from playwright.sync_api import sync_playwright
import time
import requests

def test_multiple_solves():
    # Wait for server to start
    for _ in range(10):
        try:
            requests.get("http://localhost:5000")
            break
        except:
            time.sleep(1)

    print("Server is up. Starting Playwright test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:5000")
        
        # We will solve the puzzle 6 times to see if it hangs "after 5 solutions or so"
        for i in range(1, 7):
            print(f"\n--- Attempt {i} ---")
            
            # Click Solve
            page.click("#solve-button")
            
            # Wait for either success message or failure
            # The button text changes to "Solving..." and back to "Solve Puzzle"
            try:
                page.wait_for_function(
                    "document.getElementById('solve-button').textContent === 'Solve Puzzle'", 
                    timeout=15000
                )
                
                # Check what the result message says
                result = page.locator("#result-message").inner_text()
                print(f"Result: {result.strip()}")
            except Exception as e:
                print(f"Failed or hung on attempt {i}!")
                print(e)
                break
            
            # Sleep a bit to simulate user
            time.sleep(1)
            
        print("Done testing.")
        browser.close()

if __name__ == "__main__":
    test_multiple_solves()
