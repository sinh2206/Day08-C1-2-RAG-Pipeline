"""
Automated Playwright UI Test for Streamlit RAG Chatbot (app.py)
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_streamlit_ui_with_playwright():
    project_root = Path(__file__).parent.parent
    app_py = project_root / "app.py"
    scratch_dir = project_root / ".playwright-mcp"
    scratch_dir.mkdir(exist_ok=True)
    screenshot_path = scratch_dir / "streamlit_test_result.png"

    port = "8510"
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Start Streamlit server in subprocess
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_py),
        "--server.port", port,
        "--server.headless", "true",
        "--server.enableCORS", "false"
    ]
    print(f"Starting Streamlit server on http://localhost:{port}...")
    server_proc = subprocess.Popen(cmd, cwd=str(project_root), env=env)
    time.sleep(5)

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            print("Launching Playwright Chromium Headless Browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            page.goto(f"http://localhost:{port}", wait_until="networkidle", timeout=25000)
            time.sleep(3)

            print("Verifying Header Title & Text...")
            page_text = page.inner_text("body")
            assert "Trợ Lý" in page_text or "RAG" in page_text or "Streamlit" in page_text, f"Unexpected page text: {page_text[:200]}"
            print("  ✓ Header title verified!")

            print("Taking UI screenshot...")
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  ✓ Screenshot saved: {screenshot_path}")

            browser.close()
            print("✅ Playwright UI Test Completed Successfully!")

    finally:
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    test_streamlit_ui_with_playwright()
