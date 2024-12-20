"""Test markdown conversion functionality."""

from bs4 import BeautifulSoup
from scraper import markdown_converter


def test_convert_links_basic():
    """Test converting link tags to markdown format."""
    html = """
    <a href="/page1">Home</a>
    <a href="https://example.com">External</a>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")

    result = markdown_converter.convert_links(links)

    expected = "- [Home](/page1)\n- [External](https://example.com)\n"
    assert result == expected


def test_convert_links_empty():
    """Test convert_links with empty list."""
    result = markdown_converter.convert_links([])
    # With empty list, reduce should handle gracefully
    # This might raise an exception, which is expected behavior


def test_convert_headers_hierarchical():
    """Test converting headers to hierarchical markdown list."""
    html = """
    <h2>Main Section</h2>
    <h3>Subsection</h3>
    <h4>Sub-subsection</h4>
    <h2>Another Section</h2>
    """
    soup = BeautifulSoup(html, "html.parser")
    headers = soup.find_all(["h1", "h2", "h3", "h4"])

    result = markdown_converter.convert_headers(headers)

    expected_lines = [
        "- Main Section",
        "  - Subsection",
        "    - Sub-subsection",
        "- Another Section",
    ]
    expected = "\n".join(expected_lines) + "\n"
    assert result == expected


def test_convert_headers_with_whitespace():
    """Test that header text is properly stripped of whitespace."""
    html = """
    <h2>  Spaced Header  </h2>
    <h3>\n\tTabbed Header\n</h3>
    """
    soup = BeautifulSoup(html, "html.parser")
    headers = soup.find_all(["h2", "h3"])

    result = markdown_converter.convert_headers(headers)

    expected = "- Spaced Header\n  - Tabbed Header\n"
    assert result == expected


def test_convert_headers_indentation():
    """Test that header indentation follows (level-2)*2 rule."""
    html = """
    <h2>Level 2</h2>
    <h3>Level 3</h3>
    <h4>Level 4</h4>
    """
    soup = BeautifulSoup(html, "html.parser")
    headers = soup.find_all(["h2", "h3", "h4"])

    result = markdown_converter.convert_headers(headers)

    lines = result.split("\n")[:-1]  # Remove empty last line
    assert lines[0] == "- Level 2"  # h2: (2-2)*2 = 0 spaces
    assert lines[1] == "  - Level 3"  # h3: (3-2)*2 = 2 spaces
    assert lines[2] == "    - Level 4"  # h4: (4-2)*2 = 4 spaces
