from playwright.sync_api import Page, expect, sync_playwright
import time
import pytest
import os

# To run this test:
# 1. Ensure backend is running: uvicorn deepr.backend.main:app --port 8000
# 2. Ensure frontend is running: npm run dev -- --port 3000
# 3. pytest tests/test_frontend.py

@pytest.mark.skip(reason="Requires running frontend and backend servers")
def test_ensemble_ui_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Login
        page.goto("http://localhost:3000")
        page.get_by_placeholder("test@example.com").fill("test@example.com")
        page.get_by_role("button", name="Login / Create Account").click()

        # Wait for navigation
        page.wait_for_url("http://localhost:3000/", timeout=5000)

        # 2. Setup API Key if needed
        # Check if we need to setup settings (simplification: assume we do or force it)
        page.goto("http://localhost:3000/settings")

        # Check if login redirected us back to login (session issue)
        if "/login" in page.url:
             pytest.fail("Login failed or session lost")

        # Set Key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.fail("OPENROUTER_API_KEY environment variable not set")

        page.get_by_label("API Key").fill(api_key)
        page.get_by_role("button", name="Save Configuration").click()

        expect(page.get_by_text("API Key saved successfully!")).to_be_visible(timeout=5000)

        # 3. Go to Council
        page.goto("http://localhost:3000/")

        # 4. Select Ensemble
        page.get_by_label("Ensemble").check()
        expect(page.get_by_label("Ensemble")).to_be_checked()

        # 5. Run Prompt
        page.get_by_placeholder("Enter your research question or topic...").fill("Testing Ensemble Flow")
        page.get_by_text("Start Research").click()

        # 6. Verify Execution
        expect(page.get_by_text("Initializing...")).to_be_visible()
        expect(page.get_by_text("All models are researching in parallel...", exact=False)).to_be_visible(timeout=30000)

        # 7. Verify History Badge (after completion)
        # We assume it completes or we check history later.
        # For CI, we might stop here or wait.
