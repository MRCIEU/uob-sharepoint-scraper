"""Data types for SharePoint navigation structure.

This module defines TypedDict classes that represent the structure of
navigation items extracted from SharePoint sites, both in their raw
hierarchical form and processed flat form.
"""

from typing import Any, List, Optional, TypedDict


class NavbarItem(TypedDict):
    """Represents a single navigation item in hierarchical form.

    This is the initial structure extracted from SharePoint's navigation data,
    maintaining the parent-child relationships as they exist in the original
    navigation menu.

    Attributes:
        title: Display name of the navigation item
        url: URL or path to the page (can be relative or absolute)
        is_external: Whether the link points to an external site
        base_level: Hierarchical depth of this item (0 = top level)
        children: List of nested navigation items
    """

    title: str
    url: Optional[str]
    is_external: Optional[bool]
    base_level: int
    children: List[Any]  # List[NavbarItem] - avoiding circular reference


class NavbarItemProcessed(TypedDict):
    """Represents a processed navigation item in flat form.

    This is the structure used after flattening the hierarchy and processing
    URLs for scraping and markdown generation.

    Attributes:
        title: Display name of the navigation item
        slug: URL-safe version of the title for file naming
        base_url: Original URL as extracted from SharePoint
        url: Processed absolute URL for actual navigation
        is_external: Whether the link points to an external site
        base_level: Original hierarchical depth from the navigation structure
        scrape: Whether this page should be scraped for content
        should_be_scraped: Alias for scrape field for backwards compatibility
        level: Hierarchical level for rendering (computed from base_level)
    """

    title: str
    slug: str
    base_url: Optional[str]
    url: Optional[str]
    is_external: Optional[bool]
    base_level: int
    scrape: bool
    should_be_scraped: bool  # Alias for scrape
    level: int  # For rendering
