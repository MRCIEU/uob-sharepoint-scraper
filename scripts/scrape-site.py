#!/usr/bin/env python3
"""
Scrape University of Bristol SharePoint sites and extract content.

This script automates the process of scraping SharePoint sites using Playwright,
extracting navigation structures, and saving individual pages for processing.
It handles site discovery, URL validation, and intelligent caching to avoid
unnecessary re-scraping.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page
from slugify import slugify

# Import our scraper modules
from scraper.config import SITE_ROOT
from scraper.data_types.navbar import NavbarItemProcessed
from scraper.navbar_helpers import get_pages_to_scrape
from scraper.navbar_parser import (
    get_navbar_items,
    get_quick_launch_data,
    process_navbar_items,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # ---- --site ----
    parser.add_argument(
        "--site",
        default="integrative-epidemiology",
        help="SharePoint site slug (default: integrative-epidemiology)",
    )
    # ---- --dry-run ----
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-scrape pages even if they already exist",
    )
    return parser.parse_args()


def sanitize_site_slug(site_slug: str) -> str:
    """Sanitize and validate site slug for URL and filesystem use."""
    sanitized = slugify(site_slug, separator="-")
    if not sanitized:
        raise ValueError(f"Invalid site slug: {site_slug}")
    return sanitized


def create_output_directories(site_slug: str) -> Dict[str, Path]:
    """Create necessary output directories for the site."""
    base_dir = Path("output/site-data") / site_slug
    dirs = {
        "base": base_dir,
        "pages": base_dir / "pages",
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


def setup_playwright_browser(playwright) -> Browser:
    """Set up and return a configured Playwright browser."""
    browser = playwright.chromium.launch(
        headless=False,  # Set to True for headless mode
        args=["--window-size=1920,1080"],
    )
    return browser


def is_authentication_page(page: Page) -> bool:
    """Check if current page is an authentication page."""
    url = page.url.lower()
    auth_indicators = [
        "login",
        "auth",
        "signin",
        "sso",
        "adfs",
        "microsoftonline.com",
        "account.activedirectory.windowsazure.com",
        "sts.bris.ac.uk",
    ]

    # Check URL for auth indicators
    if any(indicator in url for indicator in auth_indicators):
        return True

    # Check page content for common auth elements
    try:
        auth_selectors = [
            'input[type="email"]',
            'input[type="password"]',
            '[data-testid="i0116"]',  # Microsoft login username field
            '[data-testid="i0118"]',  # Microsoft login password field
            ".login-form",
            "#loginForm",
        ]

        for selector in auth_selectors:
            if page.locator(selector).count() > 0:
                return True

    except Exception:
        # If we can't check selectors, fall back to URL check
        pass

    return False


def handle_authentication(page: Page, site_url: str) -> None:
    """Handle authentication interactively."""
    print(f"Navigating to: {site_url}")
    page.goto(site_url)

    # Wait for initial load
    page.wait_for_load_state("networkidle")

    # Check if we're on an authentication page
    if is_authentication_page(page):
        print("=" * 60)
        print("AUTHENTICATION REQUIRED")
        print("=" * 60)
        print(
            "Please complete the authentication process in the browser window."
        )
        print("This may include:")
        print("  - Entering your University of Bristol credentials")
        print("  - Completing multi-factor authentication (MFA)")
        print("  - Accepting any additional prompts")
        print()
        print(
            "Once you've successfully authenticated and can see the SharePoint site,"
        )
        print("press Enter to continue with scraping...")
        print("=" * 60)

        input()

        # Wait for any final redirects after user input
        page.wait_for_load_state("networkidle")

        # Verify we're no longer on an auth page
        if is_authentication_page(page):
            print("Warning: Still appears to be on an authentication page.")
            print("Please ensure you've completed all authentication steps.")
            print("Press Enter to continue anyway, or Ctrl+C to abort...")
            input()

    print("Authentication check complete. Proceeding with scraping...")


def scrape_index_page(page: Page, site_url: str, output_path: Path) -> str:
    """Scrape the main site page and save HTML content."""
    print(f"Scraping index page: {site_url}")

    # Handle authentication first
    handle_authentication(page, site_url)

    html_content = page.content()

    # Save to file
    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Saved index page to: {output_path}")
    return html_content


def extract_navbar_links(
    html_content: str, site_slug: str
) -> List[NavbarItemProcessed]:
    """Extract navigation links from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract navigation data using our existing parser
    quick_launch_data = get_quick_launch_data(soup)
    navbar_items = get_navbar_items(quick_launch_data)
    processed_items = process_navbar_items(navbar_items, site_slug)

    return processed_items


def save_navbar_links(
    navbar_items: List[NavbarItemProcessed], output_path: Path
) -> None:
    """Save navbar links to JSON file."""
    # Convert to serializable format
    navbar_data = []
    for item in navbar_items:
        navbar_data.append(
            {
                "title": item["title"],
                "slug": item["slug"],
                "url": item["url"],
                "should_be_scraped": item["should_be_scraped"],
                "level": item["level"],
            }
        )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(navbar_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(navbar_data)} navbar items to: {output_path}")


def get_page_filename(url: str) -> str:
    """Generate a safe filename for a page URL."""
    # Parse URL and create a filename
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if not path_parts:
        return "index.html"

    # Use the last meaningful part of the path
    filename = path_parts[-1]
    if not filename.endswith(".html"):
        filename += ".html"

    # Sanitize for filesystem
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    return filename


def scrape_individual_pages(
    page: Page,
    navbar_items: List[NavbarItemProcessed],
    pages_dir: Path,
    force: bool = False,
) -> None:
    """Scrape individual pages that should be scraped."""
    pages_to_scrape = get_pages_to_scrape(navbar_items)

    print(f"Found {len(pages_to_scrape)} pages to scrape")

    for i, item in enumerate(pages_to_scrape, 1):
        url = item["url"]
        if not url:
            continue

        print(f"Processing page {i}/{len(pages_to_scrape)}: {item['url']}")
        filename = get_page_filename(url)
        output_path = pages_dir / filename

        # Skip if file exists and not forcing
        if output_path.exists() and not force:
            print(
                f"[{i}/{len(pages_to_scrape)}] Skipping {item['title']} "
                f"(already exists)"
            )
            continue

        try:
            print(f"[{i}/{len(pages_to_scrape)}] Scraping: {item['title']}")
            page.goto(url)
            page.wait_for_load_state("networkidle")

            # Check if we hit an auth page (session might have expired)
            if is_authentication_page(page):
                print(f"  Authentication required for {url}")
                print(
                    "  Please complete authentication and press Enter to continue..."
                )
                input()
                page.wait_for_load_state("networkidle")

            html_content = page.content()

            with output_path.open("w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"  Saved to: {filename}")

        except Exception as e:
            print(f"  Error scraping {url}: {e}")
            continue


def main() -> None:
    """Main function to orchestrate the scraping process."""
    args = parse_args()

    # Sanitize site slug
    site_slug = sanitize_site_slug(args.site)
    site_url = f"{SITE_ROOT}/sites/{site_slug}"

    print(f"Scraping site: {site_slug}")
    print(f"Site URL: {site_url}")

    if args.dry_run:
        print("DRY RUN - No actual scraping will be performed")
        print(f"Would create directories under: output/site-data/{site_slug}")
        print(f"Would scrape: {site_url}")
        return

    # ==== Setup ====
    # Create output directories
    dirs = create_output_directories(site_slug)
    print(f"Created output directories under: {dirs['base']}")

    # Set up Playwright browser
    with sync_playwright() as playwright:
        browser = setup_playwright_browser(playwright)
        page = browser.new_page()

        try:
            # ==== Scrape Index Page ====
            print("Scraping index page...")
            index_path = dirs["base"] / "index.html"
            html_content = scrape_index_page(page, site_url, index_path)

            # ==== Extract Navigation ====
            navbar_items = extract_navbar_links(html_content, site_slug)

            # Save navbar links
            navbar_path = dirs["base"] / "navbar_links.json"
            save_navbar_links(navbar_items, navbar_path)

            # ==== Scrape Individual Pages ====
            print("Scraping individual pages...")
            scrape_individual_pages(
                page, navbar_items, dirs["pages"], force=args.force
            )

            print("\nScraping completed successfully!")
            print(f"Data saved to: {dirs['base']}")

        except Exception as e:
            print(f"Error during scraping: {e}")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
