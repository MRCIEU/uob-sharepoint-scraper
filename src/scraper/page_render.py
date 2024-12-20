"""Render SharePoint page content as structured markdown.

This module combines parsed HTML content with navigation information to generate
markdown documents that represent SharePoint pages in a standardized format.
"""

import bs4

from . import general_parser, markdown_converter
from .data_types.render_data import RenderNavbarItem

# Template for the main page structure
PAGE_TEMPLATE = """
{hash} {title}

{front_matter}

**Sections**
{sections}

**Links**
{links}
"""

# Template for page metadata
PAGE_FRONT_MATTER_TEMPLATE = """
- url: {url}
"""


def render_page(soup: bs4.BeautifulSoup, page_info: RenderNavbarItem) -> str:
    """Render a SharePoint page as structured markdown.

    This function extracts headers and links from the parsed HTML and combines
    them with page metadata to create a structured markdown document.

    Args:
        soup: Parsed HTML content of the SharePoint page
        page_info: Metadata about the page including title, URL, and level

    Returns:
        String containing the complete markdown representation of the page

    The generated markdown includes:
        - Page title with appropriate heading level
        - Page metadata (URL)
        - Extracted section headers in hierarchical format
        - All meaningful links found on the page
    """
    # hash
    hash = "#" * page_info["level"]
    # front_matter
    front_matter = PAGE_FRONT_MATTER_TEMPLATE.format(url=page_info["url"])
    # sections
    header_tags = general_parser.get_headers(soup)
    section_md = markdown_converter.convert_headers(header_tags)
    # links
    href_tags = general_parser.get_hrefs(soup)
    link_md = markdown_converter.convert_links(href_tags)

    render = PAGE_TEMPLATE.format(
        hash=hash,
        title=page_info["title"],
        front_matter=front_matter,
        sections=section_md,
        links=link_md,
    )
    return render
