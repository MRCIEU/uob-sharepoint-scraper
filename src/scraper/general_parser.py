"""General-purpose HTML parsing utilities for SharePoint content.

This module provides functions to extract common HTML elements like headers
and links from SharePoint pages, which are then used in the markdown
conversion process.
"""

from typing import List, cast

import bs4
from bs4.element import Tag
from pydash import py_


def get_headers(soup: bs4.BeautifulSoup) -> List[Tag]:
    """Extract all header tags (h1-h4) from a BeautifulSoup object.

    Args:
        soup: Parsed HTML document

    Returns:
        List of header Tag elements found in the document
    """
    header_tags = ["h1", "h2", "h3", "h4"]
    header_tags_match = soup.find_all(header_tags)
    res = cast(List[Tag], header_tags_match)
    return res


def get_hrefs(soup: bs4.BeautifulSoup) -> List[Tag]:
    """Extract all meaningful links from the main article content.

    This function specifically looks for links within the main <article> tag
    and filters out empty links that are typically anchor links.

    Args:
        soup: Parsed HTML document

    Returns:
        List of link Tag elements with non-empty text content

    Raises:
        AssertionError: If no <article> tag is found in the document
    """
    main_body_match = soup.find("article")
    assert isinstance(main_body_match, Tag)
    link_tags = main_body_match.find_all("a")
    link_tags = (
        py_.chain(link_tags)
        .filter(
            # quick filter href without text, which are likely
            # header anchors
            lambda e: len(e.text.strip()) > 0
        )
        .value()
    )
    res = cast(List[Tag], link_tags)
    return res
