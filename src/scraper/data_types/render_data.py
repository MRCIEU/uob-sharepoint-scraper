"""Data types for page rendering and site structure.

This module defines the data structures used when rendering SharePoint pages
as markdown documents and managing the overall site rendering process.
"""

from typing import List, Optional, TypedDict


class RenderNavbarItem(TypedDict):
    """Represents a navigation item prepared for markdown rendering.

    This structure contains the essential information needed to render
    a page as part of a markdown document, including title, URL, and
    hierarchical level for proper heading formatting.

    Attributes:
        title: Page title to be used as heading
        slug: URL-safe identifier for the page
        url: Full URL to the page (None for linkless items)
        page_render: Rendered markdown content (None if not yet rendered)
        level: Heading level for markdown (determines number of # symbols)
    """

    title: str
    slug: str
    url: Optional[str]
    page_render: Optional[str]
    level: int


class RenderData(TypedDict):
    """Complete site rendering data structure.

    This represents the full data structure for a rendered SharePoint site,
    containing all the information needed to generate a comprehensive
    markdown representation of the site.

    Attributes:
        site_title: Human-readable name of the SharePoint site
        site_slug: URL identifier extracted from site URL
        site_url: Full URL to the SharePoint site root
        root_page_render: Rendered markdown for the site's home page
        navbar_items: All navigation items prepared for rendering

    Example:
        site_url: "https://uob.sharepoint.com/sites/integrative-epidemiology"
        site_slug: "integrative-epidemiology" (extracted from URL)
        site_title: "MRC Integrative Epidemiology Unit"
    """

    "Full render data as json / typed dict"

    # e.g. https://uob.sharepoint.com/sites/integrative-epidemiology

    # "MRC Integrative Epidemiology Unit"
    site_title: str
    # https://uob.sharepoint.com/sites/ <<integrative-epidemiology>>
    site_slug: str
    # https://uob.sharepoint.com/sites/integrative-epidemiology
    site_url: str
    # rendered root page
    root_page_render: Optional[str]
    # navbar items
    navbar_items: List[RenderNavbarItem]
