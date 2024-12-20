"""Test page rendering functionality."""

from bs4 import BeautifulSoup
from scraper import page_render


def test_render_page_basic():
    """Test basic page rendering with sample content."""
    html = """
    <html>
        <body>
            <article>
                <h2>Section 1</h2>
                <h3>Subsection</h3>
                <a href="/link1">Link 1</a>
                <a href="/link2">Link 2</a>
            </article>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    page_info = {
        "title": "Test Page",
        "slug": "test-page",
        "url": "https://example.com/test",
        "page_render": None,
        "level": 2,
    }

    result = page_render.render_page(soup, page_info)

    # Check that result contains expected sections
    assert "## Test Page" in result
    assert "- url: https://example.com/test" in result
    assert "**Sections**" in result
    assert "**Links**" in result
    assert "- Section 1" in result
    assert "- [Link 1](/link1)" in result


def test_render_page_heading_levels():
    """Test that heading levels are correctly applied."""
    html = "<html><body><article></article></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    # Test level 1 (should be single #)
    page_info_1 = {
        "title": "Level 1",
        "slug": "level-1",
        "url": "/level1",
        "page_render": None,
        "level": 1,
    }
    result_1 = page_render.render_page(soup, page_info_1)
    assert "# Level 1" in result_1

    # Test level 3 (should be triple ###)
    page_info_3 = {
        "title": "Level 3",
        "slug": "level-3",
        "url": "/level3",
        "page_render": None,
        "level": 3,
    }
    result_3 = page_render.render_page(soup, page_info_3)
    assert "### Level 3" in result_3


def test_render_page_no_content():
    """Test rendering page with no meaningful content."""
    html = """
    <html>
        <body>
            <article>
                <p>Just text, no headers or links</p>
            </article>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    page_info = {
        "title": "Empty Page",
        "slug": "empty-page",
        "url": "/empty",
        "page_render": None,
        "level": 1,
    }

    result = page_render.render_page(soup, page_info)

    # Should still have structure even with no content
    assert "# Empty Page" in result
    assert "**Sections**" in result
    assert "**Links**" in result
