"""Parse SharePoint navigation structure from HTML.

This module extracts navigation information from SharePoint pages by parsing
JavaScript data embedded in script tags, then transforms it into a structured
format suitable for generating site maps and documentation.
"""

import json
import re
from typing import Any, Dict, List, Optional

import bs4
from bs4.element import Tag
from pydash import py_

from . import navbar_helpers
from scraper.data_types.navbar import NavbarItem, NavbarItemProcessed


def get_quick_launch_data(soup: bs4.BeautifulSoup) -> List[Any]:
    """Extract navigation data from SharePoint page JavaScript.

    SharePoint embeds navigation information as JSON data within script tags.
    This function locates and parses that data to extract the site's navigation
    structure.

    Args:
        soup: Parsed HTML of a SharePoint page

    Returns:
        List containing the "quickLaunch" navigation data

    Raises:
        AssertionError: If navigation data cannot be found or parsed
    """
    script_tags = soup.find_all("script")
    print(f"{len(script_tags)=}")
    navigation_info_match = (
        py_.chain(script_tags)
        .filter(lambda e: "navigationInfo" in str(e))
        .value()
    )
    assert len(navigation_info_match) > 0, print(len(navigation_info_match))
    navigation_info: Tag = navigation_info_match[0]
    re_pattern = '"navigationInfo":(.*)(,"appBarParams")'
    re_match = re.search(re_pattern, str(navigation_info))
    assert re_match is not None
    match_groups = re_match.groups()
    assert match_groups[0] is not None
    match_group_dict = json.loads(match_groups[0])
    assert isinstance(match_group_dict, dict)
    assert "quickLaunch" in match_group_dict.keys()
    quick_launch_data = match_group_dict["quickLaunch"]
    return quick_launch_data


def extract_navbar_item(
    item: Dict[str, Any], base_level: int = 0
) -> Optional[NavbarItem]:
    """Extract and structure a single navigation item.

    Converts raw SharePoint navigation data into a structured NavbarItem format,
    handling the hierarchical nature of navigation menus.

    Args:
        item: Raw navigation item data from SharePoint
        base_level: Hierarchical level of this item (for nested navigation)

    Returns:
        Structured NavbarItem or None if the item has no title

    Note:
        This function recursively processes child navigation items to maintain
        the hierarchical structure of SharePoint navigation.
    """
    title = item["Title"]
    if title is None:
        print(f"title None, {item=}")
        return None
    is_external = None
    is_external = item["IsExternal"] if "IsExternal" in item.keys() else None
    if is_external is None:
        print(f"is_external None, {item=}")
    url = item["Url"]
    base_level = base_level
    children: List[Optional[NavbarItem]] = [
        extract_navbar_item(_, base_level=base_level + 1)
        for _ in item["Children"]
    ]
    res: NavbarItem = {
        "title": title,
        "url": url,
        "is_external": is_external,
        "base_level": base_level,
        "children": children,
    }
    return res


def get_navbar_items(
    quick_launch_data: List, base_level: int = 0
) -> List[NavbarItem]:
    """Convert raw navigation data into structured NavbarItem list.

    Processes a list of raw SharePoint navigation items and converts them
    into a list of structured NavbarItem objects, filtering out any None items.

    Args:
        quick_launch_data: Raw navigation data from SharePoint
        base_level: Starting hierarchical level (default 0)

    Returns:
        List of structured NavbarItem objects
    """
    items = [
        extract_navbar_item(_, base_level=base_level)
        for _ in quick_launch_data
    ]
    res = [_ for _ in items if _ is not None]
    return res


def process_navbar_items(
    items: List[NavbarItem], site_slug: str
) -> List[NavbarItemProcessed]:
    """Process navigation items for final output format.

    Takes structured NavbarItem objects and processes them through helper
    functions to flatten the hierarchy and update URLs for proper linking.

    Args:
        items: List of structured NavbarItem objects
        site_slug: Site identifier (e.g., 'finance-services', 'integrative-epidemiology')

    Returns:
        List of processed navigation items ready for rendering

    Example:
        site_slug examples: 'finance-services', 'integrative-epidemiology'
    """
    "site_slug example: 'finance-services', 'integrative-epidemiology'"
    processed_items = navbar_helpers.flatten_items(items)
    processed_items = navbar_helpers.update_url(
        processed_items, site_slug=site_slug
    )
    return processed_items
