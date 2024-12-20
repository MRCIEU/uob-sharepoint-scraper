from playwright.sync_api import sync_playwright

URL = "https://news.ycombinator.com"


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_load_state("networkidle")

        html_content = page.content()
        print(html_content)

        browser.close()


if __name__ == "__main__":
    main()
