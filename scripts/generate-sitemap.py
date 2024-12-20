#!/usr/bin/env python3
"""
Generate markdown sitemap from scraped SharePoint site data.

This script processes scraped SharePoint site data and generates a comprehensive
markdown document containing site structure, page content, and navigation.
It combines individual page content with the site navigation structure.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from scraper.page_render import render_page
from scraper.data_types.render_data import RenderNavbarItem, RenderData


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # ---- --site ----
    parser.add_argument(
        "--site", required=True, help="SharePoint site slug (required)"
    )
    # ---- --dry-run ----
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    return parser.parse_args()


def validate_input_directory(site_slug: str) -> Path:
    """Validate that input directory exists and contains required files."""
    input_dir = Path("output/site-data") / site_slug

    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input directory not found: {input_dir}\n"
            f"Run scrape-site.py first with --site {site_slug}"
        )

    # Check for required files
    required_files = ["index.html", "navbar_links.json"]
    missing_files = []

    for filename in required_files:
        if not (input_dir / filename).exists():
            missing_files.append(filename)

    if missing_files:
        raise FileNotFoundError(
            f"Missing required files in {input_dir}: {missing_files}\n"
            f"Run scrape-site.py first with --site {site_slug}"
        )

    return input_dir


def load_navbar_data(navbar_path: Path) -> List[Dict]:
    """Load navigation data from JSON file."""
    with navbar_path.open("r", encoding="utf-8") as f:
        navbar_data = json.load(f)

    print(f"Loaded {len(navbar_data)} navbar items from {navbar_path}")
    return navbar_data


def convert_to_render_items(navbar_data: List[Dict]) -> List[RenderNavbarItem]:
    """Convert navbar data to render format."""
    render_items = []

    for item in navbar_data:
        render_item: RenderNavbarItem = {
            "title": item["title"],
            "slug": item["slug"],
            "url": item.get("url"),
            "page_render": None,  # Will be populated later
            "level": item.get("level", 1),
        }
        render_items.append(render_item)

    return render_items


def load_page_html(page_path: Path) -> Optional[BeautifulSoup]:
    """Load and parse HTML file."""
    if not page_path.exists():
        return None

    try:
        with page_path.open("r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        return soup
    except Exception as e:
        print(f"Error loading {page_path}: {e}")
        return None


def get_page_filename_from_url(url: Optional[str]) -> str:
    """Generate page filename from URL (same logic as scrape-site.py)."""
    if not url:
        return "index.html"

    from urllib.parse import urlparse
    import re

    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if not path_parts:
        return "index.html"

    filename = path_parts[-1]
    if not filename.endswith(".html"):
        filename += ".html"

    # Sanitize for filesystem
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    return filename


def render_pages(
    render_items: List[RenderNavbarItem], input_dir: Path
) -> List[RenderNavbarItem]:
    """Render individual pages with their content."""
    pages_dir = input_dir / "pages"
    rendered_items = []

    for item in render_items:
        # Skip items without URLs
        if not item["url"]:
            rendered_items.append(item)
            continue

        # Get the page HTML file
        filename = get_page_filename_from_url(item["url"])
        page_path = pages_dir / filename

        # Load and render the page
        soup = load_page_html(page_path)
        if soup:
            try:
                rendered_content = render_page(soup, item)
                item["page_render"] = rendered_content
                print(f"Rendered: {item['title']}")
            except Exception as e:
                print(f"Error rendering {item['title']}: {e}")
                item["page_render"] = f"Error rendering page: {e}"
        else:
            print(f"Could not load HTML for: {item['title']} ({filename})")
            item["page_render"] = "Page content not available"

        rendered_items.append(item)

    return rendered_items


def render_index_page(input_dir: Path) -> str:
    """Render the main index page."""
    index_path = input_dir / "index.html"
    soup = load_page_html(index_path)

    if not soup:
        return "Index page content not available"

    # Create a render item for the index page
    index_item: RenderNavbarItem = {
        "title": "Home",
        "slug": "home",
        "url": None,  # Index page doesn't have a specific URL
        "page_render": None,
        "level": 1,
    }

    try:
        return render_page(soup, index_item)
    except Exception as e:
        return f"Error rendering index page: {e}"


def generate_full_sitemap(render_data: RenderData) -> str:
    """Generate the complete sitemap markdown."""
    sitemap_template = """# {site_title}

- Site: {site_url}
- Slug: {site_slug}

## Home Page

{root_page_render}

## Site Navigation

{navigation_content}
"""

    # Generate navigation content
    navigation_parts = []
    for item in render_data["navbar_items"]:
        if item["page_render"]:
            navigation_parts.append(item["page_render"])
        else:
            # Just add the title if no content
            hash_symbols = "#" * (
                item["level"] + 1
            )  # +1 because we start with ##
            navigation_parts.append(
                f"{hash_symbols} {item['title']}\n\n- url: {item['url']}\n"
            )

    navigation_content = "\n\n".join(navigation_parts)

    # Fill in the template
    sitemap = sitemap_template.format(
        site_title=render_data["site_title"],
        site_url=render_data["site_url"],
        site_slug=render_data["site_slug"],
        root_page_render=render_data["root_page_render"]
        or "Home page content not available",
        navigation_content=navigation_content,
    )

    return sitemap


def save_sitemap(sitemap_content: str, output_path: Path) -> None:
    """Save the sitemap to file."""
    with output_path.open("w", encoding="utf-8") as f:
        f.write(sitemap_content)

    print(f"Sitemap saved to: {output_path}")


def extract_site_title_from_index(index_path: Path) -> str:
    """Extract site title from index HTML."""
    soup = load_page_html(index_path)
    if not soup:
        return "Unknown Site"

    # Try to find title tag
    title_tag = soup.find("title")
    if title_tag and title_tag.text.strip():
        return title_tag.text.strip()

    # Try to find h1 tag
    h1_tag = soup.find("h1")
    if h1_tag and h1_tag.text.strip():
        return h1_tag.text.strip()

    return "Unknown Site"


def main() -> None:
    """Main function to orchestrate the sitemap generation."""
    args = parse_args()

    print(f"Generating sitemap for site: {args.site}")

    if args.dry_run:
        print("DRY RUN - No files will be created")
        print(f"Would process: output/site-data/{args.site}")
        print(f"Would create: output/{args.site}.md")
        return

    # ==== Validate Input ====
    input_dir = validate_input_directory(args.site)
    print(f"Using input directory: {input_dir}")

    # ==== Load Navigation Data ====
    navbar_path = input_dir / "navbar_links.json"
    navbar_data = load_navbar_data(navbar_path)

    # Convert to render format
    render_items = convert_to_render_items(navbar_data)

    # ==== Render Pages ====
    print("Rendering individual pages...")
    rendered_items = render_pages(render_items, input_dir)

    # ==== Render Index Page ====
    print("Rendering index page...")
    root_page_render = render_index_page(input_dir)

    # ==== Extract Site Information ====
    site_title = extract_site_title_from_index(input_dir / "index.html")
    site_url = f"https://uob.sharepoint.com/sites/{args.site}"

    # ==== Create Render Data Structure ====
    render_data: RenderData = {
        "site_title": site_title,
        "site_slug": args.site,
        "site_url": site_url,
        "root_page_render": root_page_render,
        "navbar_items": rendered_items,
    }

    # ==== Generate Full Sitemap ====
    print("Generating complete sitemap...")
    sitemap_content = generate_full_sitemap(render_data)

    # ==== Save Output ====
    output_path = Path("output") / f"{args.site}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_sitemap(sitemap_content, output_path)

    print("\nSitemap generation completed successfully!")
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
