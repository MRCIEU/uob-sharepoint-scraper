#!/usr/bin/env python3
"""
Process all University of Bristol SharePoint sites listed in SITES.txt.

This script automates the complete processing pipeline for multiple SharePoint
sites. It reads the site list from SITES.txt, and for each site runs both
scraping and sitemap generation steps. By default, it skips sites that
already have data in the output directory unless --force is specified.

This version handles authentication properly by importing and reusing functions
from scrape-site.py to maintain a persistent browser session across all sites.
"""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from playwright.sync_api import sync_playwright, Browser

# Import our scraper modules
from scraper.config import SITE_ROOT


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # ---- --dry-run ----
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    # ---- --force ----
    parser.add_argument(
        "--force",
        choices=["all", "scrape", "generate"],
        help=(
            "Force processing: 'all' for both steps, "
            "'scrape' for scraping only, 'generate' for sitemap only"
        ),
    )
    # ---- --scrape-force ----
    parser.add_argument(
        "--scrape-force",
        action="store_true",
        help="Re-scrape individual pages even if they already exist",
    )
    return parser.parse_args()


def load_scrape_site_module():
    """Load the scrape-site.py module using importlib."""
    script_path = Path(__file__).parent / "scrape-site.py"
    spec = importlib.util.spec_from_file_location("scrape_site", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load scrape-site.py from {script_path}")

    scrape_site_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scrape_site_module)
    return scrape_site_module


def load_sites_list() -> List[str]:
    """Load site slugs from SITES.txt file."""
    sites_file = Path("SITES.txt")

    if not sites_file.exists():
        raise FileNotFoundError(
            f"SITES.txt not found in current directory: {Path.cwd()}"
        )

    sites = []
    with sites_file.open("r", encoding="utf-8") as f:
        for line in f:
            site = line.strip()
            if site and not site.startswith(
                "#"
            ):  # Skip empty lines and comments
                sites.append(site)

    if not sites:
        raise ValueError("No valid sites found in SITES.txt")

    print(f"Loaded {len(sites)} sites from SITES.txt")
    return sites


def check_site_data_exists(site_slug: str) -> dict:
    """Check what data already exists for a site."""
    base_dir = Path("output/site-data") / site_slug
    sitemap_file = Path("output") / f"{site_slug}.md"

    return {
        "site_data": base_dir.exists() and (base_dir / "index.html").exists(),
        "sitemap": sitemap_file.exists(),
    }


def should_process_site(
    site_slug: str, force_option: Optional[str], step: str
) -> bool:
    """Determine if a site should be processed for a given step."""
    if force_option == "all":
        return True
    if force_option == step:
        return True

    # Check if data already exists
    existing_data = check_site_data_exists(site_slug)

    if step == "scrape":
        return not existing_data["site_data"]
    elif step == "generate":
        # Need both site data and no existing sitemap
        return existing_data["site_data"] and not existing_data["sitemap"]

    return False


def scrape_site_internal(
    site_slug: str,
    browser: Optional[Browser],
    scrape_force: bool = False,
    dry_run: bool = False,
    scrape_module=None,
) -> bool:
    """Internal function to scrape a single site using existing browser."""
    if dry_run:
        print(f"  [DRY RUN] Would scrape site: {site_slug}")
        return True

    if browser is None:
        print(f"  ✗ No browser available for scraping {site_slug}")
        return False

    if scrape_module is None:
        print(f"  ✗ No scrape module available for scraping {site_slug}")
        return False

    try:
        # Sanitize site slug
        site_slug = scrape_module.sanitize_site_slug(site_slug)
        site_url = f"{SITE_ROOT}/sites/{site_slug}"

        print(f"  Scraping site: {site_slug}")
        print(f"  Site URL: {site_url}")

        # Create output directories
        dirs = scrape_module.create_output_directories(site_slug)
        print(f"  Created output directories under: {dirs['base']}")

        # Create a new page for this site
        page = browser.new_page()

        try:
            # Scrape Index Page
            print("  Scraping index page...")
            index_path = dirs["base"] / "index.html"
            html_content = scrape_module.scrape_index_page(
                page, site_url, index_path
            )

            # Extract Navigation
            navbar_items = scrape_module.extract_navbar_links(
                html_content, site_slug
            )

            # Save navbar links
            navbar_path = dirs["base"] / "navbar_links.json"
            scrape_module.save_navbar_links(navbar_items, navbar_path)

            # Scrape Individual Pages
            print("  Scraping individual pages...")
            scrape_module.scrape_individual_pages(
                page, navbar_items, dirs["pages"], force=scrape_force
            )

            print(f"  ✓ Scraping completed successfully for {site_slug}")
            print(f"  Data saved to: {dirs['base']}")
            return True

        finally:
            page.close()

    except Exception as e:
        print(f"  ✗ Error during scraping {site_slug}: {e}")
        return False


def run_command(
    cmd: List[str], description: str, dry_run: bool = False
) -> bool:
    """Run a command and return success status."""
    print(f"  {description}...")

    if dry_run:
        print(f"    [DRY RUN] Would run: {' '.join(cmd)}")
        return True

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"    ✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ✗ {description} failed:")
        print(f"      Command: {' '.join(cmd)}")
        print(f"      Return code: {e.returncode}")
        if e.stdout:
            print(f"      Stdout: {e.stdout}")
        if e.stderr:
            print(f"      Stderr: {e.stderr}")
        return False


def process_site(
    site_slug: str,
    force_option: Optional[str],
    scrape_force: bool = False,
    dry_run: bool = False,
    browser: Optional[Browser] = None,
    scrape_module=None,
) -> dict:
    """Process a single site through scraping and sitemap generation."""
    print(f"\nProcessing site: {site_slug}")
    print("=" * 50)

    results = {"scrape": False, "generate": False}

    # ---- Check current state ----
    existing_data = check_site_data_exists(site_slug)
    print(f"  Site data exists: {existing_data['site_data']}")
    print(f"  Sitemap exists: {existing_data['sitemap']}")

    # ---- Scraping step ----
    if should_process_site(site_slug, force_option, "scrape"):
        # Use internal scraping function
        results["scrape"] = scrape_site_internal(
            site_slug, browser, scrape_force, dry_run, scrape_module
        )

        if not results["scrape"] and not dry_run:
            print("  ✗ Skipping sitemap generation due to scraping failure")
            return results
    else:
        print("  ⏭ Skipping scraping (data exists or not forced)")
        results["scrape"] = True  # Consider it successful if skipped

    # ---- Sitemap generation step ----
    if should_process_site(site_slug, force_option, "generate"):
        cmd = [
            "uv",
            "run",
            "python",
            "scripts/generate-sitemap.py",
            "--site",
            site_slug,
        ]
        if dry_run:
            cmd.append("--dry-run")

        results["generate"] = run_command(
            cmd, f"Generating sitemap for {site_slug}", dry_run
        )
    else:
        print("  ⏭ Skipping sitemap generation (sitemap exists or no data)")
        results["generate"] = True  # Consider it successful if skipped

    return results


def print_summary(sites: List[str], all_results: dict, dry_run: bool) -> None:
    """Print processing summary."""
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    if dry_run:
        print("(DRY RUN - No actual processing performed)")
        print()

    successful_scrapes = 0
    successful_generates = 0
    total_sites = len(sites)

    for site in sites:
        results = all_results.get(site, {"scrape": False, "generate": False})
        scrape_status = "✓" if results["scrape"] else "✗"
        generate_status = "✓" if results["generate"] else "✗"

        print(
            f"  {site:25} | Scrape: {scrape_status} | Generate: {generate_status}"
        )

        if results["scrape"]:
            successful_scrapes += 1
        if results["generate"]:
            successful_generates += 1

    print()
    print(f"Sites processed: {total_sites}")
    print(f"Successful scrapes: {successful_scrapes}/{total_sites}")
    print(f"Successful generates: {successful_generates}/{total_sites}")

    if not dry_run:
        if (
            successful_scrapes == total_sites
            and successful_generates == total_sites
        ):
            print("\n🎉 All sites processed successfully!")
        else:
            print("\n⚠️ Some sites had issues. Check the logs above.")


def main() -> None:
    """Main function to orchestrate processing of all sites."""
    args = parse_args()

    print("UoB SharePoint Sites - Batch Processor")
    print("=" * 60)

    try:
        # ---- Load scrape-site module ----
        print("Loading scrape-site module...")
        scrape_module = load_scrape_site_module()
        print("✓ Scrape module loaded successfully")

        # ---- Load sites list ----
        sites = load_sites_list()

        if args.dry_run:
            print("DRY RUN MODE - No actual processing will be performed")
            print()

        if args.force:
            print(f"Force mode: {args.force}")
            print()

        if args.scrape_force:
            print("Scrape force mode: Will re-scrape individual pages")
            print()

        # ---- Process each site ----
        all_results = {}

        # Set up browser once for all sites to handle authentication properly
        browser = None
        playwright_instance = None
        if not args.dry_run:
            print("Setting up browser for authentication handling...")
            playwright_instance = sync_playwright().start()
            browser = scrape_module.setup_playwright_browser(
                playwright_instance
            )
            print(
                "Browser ready. Authentication will be handled interactively."
            )
            print()

        try:
            for i, site in enumerate(sites, 1):
                print(f"\n[{i}/{len(sites)}]", end=" ")

                try:
                    results = process_site(
                        site,
                        args.force,
                        args.scrape_force,
                        args.dry_run,
                        browser,
                        scrape_module,
                    )
                    all_results[site] = results
                except Exception as e:
                    print(f"  ✗ Error processing {site}: {e}")
                    all_results[site] = {"scrape": False, "generate": False}

        finally:
            # Clean up browser
            if browser:
                browser.close()
            if playwright_instance:
                playwright_instance.stop()

        # ---- Print summary ----
        print_summary(sites, all_results, args.dry_run)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
