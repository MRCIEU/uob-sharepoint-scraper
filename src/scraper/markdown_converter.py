"""Convert HTML elements to markdown format for SharePoint content.

This module handles the conversion of extracted HTML elements (links and headers)
into markdown format, suitable for creating structured documentation from
SharePoint sites.
"""

from typing import List

from pydash import py_
from bs4.element import Tag


def convert_links(link_tags: List[Tag]) -> str:
    """Convert a list of HTML link tags to markdown format.

    Transforms HTML <a> tags into markdown link format: [text](url)
    Each link is prefixed with "- " to create a markdown list.

    Args:
        link_tags: List of BeautifulSoup Tag objects representing <a> elements

    Returns:
        String containing markdown-formatted links, each on a new line

    Example:
        Input: [<a href="/page.aspx">Home</a>, <a href="https://example.com">External</a>]
        Output: "- [Home](/page.aspx)\n- [External](https://example.com)\n"
    """
    if not link_tags:
        return ""

    def _convert(tag: Tag) -> str:
        text = tag.text
        href = tag.get("href")
        res = "- [{desc}]({url})\n".format(desc=text, url=href)
        return res

    doc = py_.chain(link_tags).map(_convert).reduce(lambda a, b: a + b).value()
    res = doc
    return res


def convert_headers(header_tags: List[Tag]) -> str:
    """Convert a list of HTML header tags to markdown format.

    Transforms HTML header tags (h1-h6) into a hierarchical markdown list
    structure with proper indentation based on header level.

    Args:
        header_tags: List of BeautifulSoup Tag objects representing header elements

    Returns:
        String containing markdown-formatted headers as an indented list

    Example:
        Input: [<h2>Main Section</h2>, <h3>Subsection</h3>]
        Output: "- Main Section\n  - Subsection\n"

    Note:
        - h2 elements have no indentation (base level)
        - h3 elements have 2 spaces indentation
        - h4 elements have 4 spaces indentation, etc.
    """
    if not header_tags:
        return ""

    def _convert(tag: Tag) -> str:
        header_tag_name = tag.name
        header_level = int(header_tag_name[1:])
        assert header_level >= 2, print(header_level)
        indent_level = header_level - 2
        label = tag.text.strip()
        res = "{indent}- {label}\n".format(
            indent="  " * indent_level, label=label
        )
        return res

    doc = (
        py_.chain(header_tags).map(_convert).reduce(lambda a, b: a + b).value()
    )
    res = doc
    return res
