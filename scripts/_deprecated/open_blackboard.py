from playwright.sync_api import sync_playwright
import sys

p = sync_playwright().start()
browser = p.chromium.launch(
    headless=False,
    args=["--start-maximized"],
)
# Incognito: new_context with no stored state
context = browser.new_context(no_viewport=True)
page = context.new_page()
page.goto("https://blackboard.sc.edu/")
print("READY: Browser open at blackboard.sc.edu", flush=True)

# Keep alive, respond to commands on stdin
try:
    for line in sys.stdin:
        line = line.strip()
        if line == "quit":
            break
        elif line == "status":
            print(f"STATUS: title={page.title()}, url={page.url}", flush=True)
except KeyboardInterrupt:
    pass

browser.close()
p.stop()
