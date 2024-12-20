"""Helper functions for processing SharePoint navigation data.

This module provides utilities for transforming hierarchical navigation data
into a flat structure suitable for generating site maps and updating URLs
for proper linking within the SharePoint scraper system.
"""

from typing import Any, List

from scraper.data_types.navbar import NavbarItem, NavbarItemProcessed
from pydash import py_
from slugify import slugify

from . import config


def flatten_items(
    items: List[NavbarItem],
) -> List[NavbarItemProcessed]:
    """Flatten hierarchical navigation items into a flat list.

    Recursively processes nested navigation items and converts them into
    a flat list of NavbarItemProcessed objects, maintaining parent-child
    relationships through the flattened structure.

    Args:
        items: List of hierarchical NavbarItem objects

    Returns:
        Flattened list of NavbarItemProcessed objects

    Note:
        Each item in the hierarchy becomes a separate entry in the flat list,
        including both parent items and all their children recursively.
    """

    def _transform(
        item: NavbarItem,
    ) -> List[Any]:
        parent = [
            {
                "title": item["title"],
                "slug": slugify(item["title"]),
                "base_url": item["url"],
                "url": item["url"],
                "is_external": item["is_external"],
                "base_level": item["base_level"],
                "scrape": False,
                "should_be_scraped": False,
                "level": item["base_level"] + 1,  # For markdown headings
            }
        ]
        children = [_transform(_) for _ in item["children"]]
        res = parent + children
        return res

    res = py_.chain(items).map(_transform).flatten_deep().value()
    return res


def update_url(
    items: List[NavbarItemProcessed], site_slug: str
) -> List[NavbarItemProcessed]:
    """Update URLs in navigation items for proper linking and scraping flags.

    Processes navigation items to:
    1. Convert relative URLs to absolute URLs using the site root
    2. Determine which pages should be scraped based on URL patterns
    3. Filter out blocked pages that shouldn't be processed
    4. Handle special cases like linkless headers

    Args:
        items: List of navigation items to process
        site_slug: Site identifier used to determine scraping eligibility

    Returns:
        Updated list of navigation items with proper URLs and scraping flags

    The function applies these rules:
    - URLs starting with "/sites/" are made absolute using SITE_ROOT
    - Pages ending with ".aspx" in the target site are marked for scraping
    - Certain blocked pages (AllItems.aspx, admin-centre.aspx, news.aspx) are excluded
    - Linkless headers are converted to None URLs
    """
    for item in items:
        if item["base_url"] is not None:
            if item["base_url"].startswith("/sites/"):
                item["url"] = config.SITE_ROOT + item["base_url"]
            if item["base_url"].startswith("/sites/" + site_slug) and item[
                "base_url"
            ].endswith(".aspx"):
                item["scrape"] = True
                item["should_be_scraped"] = True
            block_pages = ["AllItems.aspx", "admin-centre.aspx", "news.aspx"]
            in_block_pages = (
                py_.chain(block_pages)
                .map(
                    lambda e: item["base_url"] is not None
                    and item["base_url"].endswith(e)
                )
                .some()
                .value()
            )
            if in_block_pages:
                item["scrape"] = False
                item["should_be_scraped"] = False
            block_urls = ["http://linkless.header/"]
            if item["base_url"] in block_urls:
                item["url"] = None
    return items


def get_pages_to_scrape(
    items: List[NavbarItemProcessed],
) -> List[NavbarItemProcessed]:
    """Filter navigation items to get only pages that should be scraped.

    Args:
        items: List of processed navigation items

    Returns:
        List of items that should be scraped (have scrape=True and valid URL)
    """
    return [
        item for item in items if item.get("scrape", False) and item.get("url")
    ]
