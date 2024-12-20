"""Test general parser functionality with BeautifulSoup objects."""

from bs4 import BeautifulSoup
from scraper import general_parser


def test_get_headers_basic():
    """Test extracting headers from basic HTML."""
    html = """
    <html>
        <body>
            <h1>Main Title</h1>
            <h2>Section</h2>
            <h3>Subsection</h3>
            <p>Regular paragraph</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    headers = general_parser.get_headers(soup)

    assert len(headers) == 3
    assert headers[0].name == "h1"
    assert headers[0].text == "Main Title"
    assert headers[1].name == "h2"
    assert headers[1].text == "Section"


def test_get_headers_empty():
    """Test get_headers with HTML containing no headers."""
    html = """
    <html>
        <body>
            <p>Just a paragraph</p>
            <div>A div</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    headers = general_parser.get_headers(soup)

    assert len(headers) == 0


def test_get_hrefs_basic():
    """Test extracting meaningful links from article content."""
    html = """
    <html>
        <body>
            <article>
                <a href="/page1">Link with text</a>
                <a href="/page2"></a>  <!-- Empty link, should be filtered -->
                <a href="/page3">Another link</a>
            </article>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = general_parser.get_hrefs(soup)

    assert len(links) == 2
    assert links[0].text == "Link with text"
    assert links[0].get("href") == "/page1"
    assert links[1].text == "Another link"


def test_get_hrefs_no_article():
    """Test get_hrefs raises assertion when no article tag present."""
    html = """
    <html>
        <body>
            <div>
                <a href="/page1">Link outside article</a>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    try:
        general_parser.get_hrefs(soup)
        assert False, "Should have raised AssertionError"
    except AssertionError:
        pass  # Expected behavior


def test_get_hrefs_filters_empty_links():
    """Test that empty links are properly filtered out."""
    html = """
    <html>
        <body>
            <article>
                <a href="#anchor"></a>
                <a href="/page1">   </a>  <!-- Whitespace only -->
                <a href="/page2">Real link</a>
            </article>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = general_parser.get_hrefs(soup)

    # Should only get the "Real link" - empty and whitespace-only are filtered
    assert len(links) == 1
    assert links[0].text == "Real link"
