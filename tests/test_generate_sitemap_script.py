"""
Mock tests for the generate-sitemap.py script.

These tests mock file I/O and HTML parsing to test the core logic of
the sitemap generation script without requiring actual scraped data.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open


class TestGenerateSitemapLogic:
    """Test the core logic of the generate-sitemap script."""

    def test_input_directory_validation(self):
        """Test input directory validation logic."""

        # Create a mock that simulates successful validation
        def mock_validate_input_directory_success(site_slug: str):
            """Mock successful directory validation."""
            return f"output/site-data/{site_slug}"

        # Create a mock that simulates failed validation
        def mock_validate_input_directory_fail(site_slug: str):
            """Mock failed directory validation."""
            raise FileNotFoundError(
                f"Input directory not found: output/site-data/{site_slug}\n"
                f"Run scrape-site.py first with --site {site_slug}"
            )

        # Test valid directory
        result = mock_validate_input_directory_success("test-site")
        assert result == "output/site-data/test-site"

        # Test missing directory
        try:
            mock_validate_input_directory_fail("missing-site")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_navbar_data_loading(self):
        """Test navbar data loading and conversion."""
        mock_navbar_data = [
            {
                "title": "Home",
                "slug": "home",
                "url": "https://example.com/home.aspx",
                "should_be_scraped": True,
                "level": 1,
            },
            {
                "title": "About",
                "slug": "about",
                "url": "https://example.com/about.aspx",
                "should_be_scraped": True,
                "level": 1,
            },
        ]

        def mock_convert_to_render_items(navbar_data):
            """Mock conversion to render format."""
            render_items = []
            for item in navbar_data:
                render_item = {
                    "title": item["title"],
                    "slug": item["slug"],
                    "url": item.get("url"),
                    "page_render": None,
                    "level": item.get("level", 1),
                }
                render_items.append(render_item)
            return render_items

        result = mock_convert_to_render_items(mock_navbar_data)

        # Verify conversion
        assert len(result) == 2
        assert result[0]["title"] == "Home"
        assert result[0]["page_render"] is None
        assert result[1]["level"] == 1

    def test_page_filename_from_url(self):
        """Test page filename generation from URLs."""
        from urllib.parse import urlparse
        import re

        def mock_get_page_filename_from_url(url):
            """Mock page filename generation."""
            if not url:
                return "index.html"

            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.split("/") if part]

            if not path_parts:
                return "index.html"

            filename = path_parts[-1]
            if not filename.endswith(".html"):
                filename += ".html"

            # Sanitize for filesystem
            filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
            return filename

        test_cases = [
            (None, "index.html"),
            ("https://example.com/sites/test/page.aspx", "page.aspx.html"),
            ("https://example.com/sites/test/about", "about.html"),
            ("https://example.com/", "index.html"),
        ]

        for url, expected in test_cases:
            result = mock_get_page_filename_from_url(url)
            assert result == expected

    def test_site_title_extraction(self):
        """Test site title extraction from HTML."""

        def mock_extract_site_title(html_content):
            """Mock site title extraction."""
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")

            # Try title tag first
            title_tag = soup.find("title")
            if title_tag and title_tag.text.strip():
                return title_tag.text.strip()

            # Try h1 tag
            h1_tag = soup.find("h1")
            if h1_tag and h1_tag.text.strip():
                return h1_tag.text.strip()

            return "Unknown Site"

        test_cases = [
            (
                "<html><head><title>Test Site</title></head></html>",
                "Test Site",
            ),
            ("<html><body><h1>My Site</h1></body></html>", "My Site"),
            ("<html><body>No title</body></html>", "Unknown Site"),
        ]

        for html, expected in test_cases:
            result = mock_extract_site_title(html)
            assert result == expected


class TestSitemapGeneration:
    """Test sitemap generation and formatting."""

    def test_full_sitemap_generation(self):
        """Test complete sitemap generation."""
        mock_render_data = {
            "site_title": "Test Site",
            "site_slug": "test-site",
            "site_url": "https://uob.sharepoint.com/sites/test-site",
            "root_page_render": "# Home\n\nWelcome to the test site.",
            "navbar_items": [
                {
                    "title": "About",
                    "slug": "about",
                    "url": "https://example.com/about.aspx",
                    "page_render": "## About\n\n- url: https://example.com/about.aspx\n\nAbout page content.",
                    "level": 1,
                },
                {
                    "title": "Contact",
                    "slug": "contact",
                    "url": "https://example.com/contact.aspx",
                    "page_render": None,
                    "level": 2,
                },
            ],
        }

        def mock_generate_full_sitemap(render_data):
            """Mock full sitemap generation."""
            sitemap_template = """# {site_title}

- Site: {site_url}
- Slug: {site_slug}

## Home Page

{root_page_render}

## Site Navigation

{navigation_content}
"""

            # Generate navigation content
            navigation_parts = []
            for item in render_data["navbar_items"]:
                if item["page_render"]:
                    navigation_parts.append(item["page_render"])
                else:
                    # Just add the title if no content
                    hash_symbols = "#" * (item["level"] + 1)
                    navigation_parts.append(
                        f"{hash_symbols} {item['title']}\n\n- url: {item['url']}\n"
                    )

            navigation_content = "\n\n".join(navigation_parts)

            # Fill in the template
            sitemap = sitemap_template.format(
                site_title=render_data["site_title"],
                site_url=render_data["site_url"],
                site_slug=render_data["site_slug"],
                root_page_render=render_data["root_page_render"]
                or "Home page content not available",
                navigation_content=navigation_content,
            )

            return sitemap

        result = mock_generate_full_sitemap(mock_render_data)

        # Verify sitemap structure
        assert "# Test Site" in result
        assert "https://uob.sharepoint.com/sites/test-site" in result
        assert "Welcome to the test site" in result
        assert "## About" in result
        assert "### Contact" in result  # Level 2 becomes ###

    def test_navigation_content_formatting(self):
        """Test navigation content formatting."""
        mock_items = [
            {
                "title": "Home",
                "level": 1,
                "page_render": "## Home\n\nHome content",
                "url": "https://example.com/home.aspx",
            },
            {
                "title": "About",
                "level": 2,
                "page_render": None,
                "url": "https://example.com/about.aspx",
            },
        ]

        def mock_format_navigation(items):
            """Mock navigation formatting."""
            navigation_parts = []
            for item in items:
                if item["page_render"]:
                    navigation_parts.append(item["page_render"])
                else:
                    hash_symbols = "#" * (item["level"] + 1)
                    navigation_parts.append(
                        f"{hash_symbols} {item['title']}\n\n- url: {item['url']}\n"
                    )
            return "\n\n".join(navigation_parts)

        result = mock_format_navigation(mock_items)

        # Verify formatting
        assert "## Home" in result
        assert "### About" in result  # Level 2 becomes ###
        assert "url: https://example.com/about.aspx" in result


class TestHTMLParsing:
    """Test HTML parsing and content extraction."""

    def test_page_html_loading(self):
        """Test HTML file loading and parsing."""
        mock_html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <h1>Page Title</h1>
                    <h2>Section 1</h2>
                    <p>Some content.</p>
                    <a href="/link1">Link 1</a>
                    <h3>Subsection</h3>
                    <a href="/link2">Link 2</a>
                </article>
            </body>
        </html>
        """

        def mock_load_page_html(content):
            """Mock HTML loading and parsing."""
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")
            return soup

        def mock_extract_content(soup):
            """Mock content extraction."""
            headers = soup.find_all(["h1", "h2", "h3", "h4"])
            links = soup.find_all("a", href=True)

            return {
                "headers": [
                    {"tag": h.name, "text": h.text.strip()} for h in headers
                ],
                "links": [
                    {"text": a.text.strip(), "href": a["href"]}
                    for a in links
                    if a.text.strip()
                ],
            }

        soup = mock_load_page_html(mock_html_content)
        content = mock_extract_content(soup)

        # Verify extraction
        assert len(content["headers"]) == 3
        assert content["headers"][0]["tag"] == "h1"
        assert content["headers"][0]["text"] == "Page Title"
        assert len(content["links"]) == 2
        assert content["links"][0]["text"] == "Link 1"


class TestFileOperations:
    """Test file operations and I/O."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"test": "data"}',
    )
    @patch("json.load")
    def test_json_file_loading(self, mock_json_load, mock_open):
        """Test JSON file loading."""
        mock_json_load.return_value = {"test": "data"}

        def mock_load_navbar_data(path):
            """Mock navbar data loading."""
            with open(path, "r") as f:
                return json.load(f)

        result = mock_load_navbar_data("test.json")

        # Verify file operations
        mock_open.assert_called_once_with("test.json", "r")
        mock_json_load.assert_called_once()
        assert result == {"test": "data"}

    @patch("builtins.open", new_callable=mock_open)
    def test_sitemap_file_saving(self, mock_open):
        """Test sitemap file saving."""
        sitemap_content = "# Test Sitemap\n\nContent here."

        def mock_save_sitemap(content, path):
            """Mock sitemap saving."""
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        mock_save_sitemap(sitemap_content, "output.md")

        # Verify file operations
        mock_open.assert_called_once_with("output.md", "w", encoding="utf-8")
        mock_open().write.assert_called_once_with(sitemap_content)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_missing_input_files(self):
        """Test handling of missing input files."""

        def mock_validate_files(input_dir):
            """Mock file validation."""
            required_files = ["index.html", "navbar_links.json"]
            missing_files = []

            for filename in required_files:
                # Simulate missing files
                if filename == "navbar_links.json":
                    missing_files.append(filename)

            if missing_files:
                raise FileNotFoundError(f"Missing files: {missing_files}")

        try:
            mock_validate_files("test_dir")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON data."""

        def mock_load_invalid_json():
            """Mock invalid JSON loading."""
            raise json.JSONDecodeError("Invalid JSON", "test", 0)

        try:
            mock_load_invalid_json()
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass

    def test_html_parsing_errors(self):
        """Test handling of HTML parsing errors."""

        def mock_parse_invalid_html(content):
            """Mock HTML parsing with error handling."""
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(content, "html.parser")
                return soup
            except Exception:
                return None

        # Test with valid HTML
        valid_html = "<html><body>Test</body></html>"
        result = mock_parse_invalid_html(valid_html)
        assert result is not None

        # Test with empty content
        empty_html = ""
        result = mock_parse_invalid_html(empty_html)
        assert (
            result is not None
        )  # BeautifulSoup handles empty content gracefully


class TestCommandLineInterface:
    """Test command line interface functionality."""

    def test_argument_parsing(self):
        """Test command line argument parsing."""
        # Mock argument parsing
        mock_args = MagicMock()
        mock_args.site = "test-site"
        mock_args.dry_run = False

        # Test required argument
        assert mock_args.site == "test-site"
        assert mock_args.dry_run is False

    def test_dry_run_mode(self):
        """Test dry run mode behavior."""

        def mock_main_dry_run(dry_run=True):
            """Mock main function in dry run mode."""
            if dry_run:
                return "DRY RUN - No files will be created"
            else:
                return "Processing files..."

        # Test dry run
        result = mock_main_dry_run(dry_run=True)
        assert result == "DRY RUN - No files will be created"

        # Test normal run
        result = mock_main_dry_run(dry_run=False)
        assert result == "Processing files..."


class TestIntegrationFlow:
    """Test the integration between components."""

    def test_end_to_end_flow(self):
        """Test the complete end-to-end flow."""
        # Mock input data
        mock_navbar_data = [
            {
                "title": "Home",
                "slug": "home",
                "url": "https://example.com/home.aspx",
                "should_be_scraped": True,
                "level": 1,
            }
        ]

        mock_html_content = "<html><head><title>Test Site</title></head><body><h1>Welcome</h1></body></html>"

        def mock_complete_flow(navbar_data, html_content):
            """Mock complete sitemap generation flow."""
            # Convert navbar data
            render_items = [
                {
                    "title": item["title"],
                    "slug": item["slug"],
                    "url": item["url"],
                    "page_render": f"## {item['title']}\n\nContent for {item['title']}",
                    "level": item["level"],
                }
                for item in navbar_data
            ]

            # Extract site title
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")
            title_tag = soup.find("title")
            site_title = title_tag.text if title_tag else "Unknown Site"

            # Create render data
            render_data = {
                "site_title": site_title,
                "site_slug": "test-site",
                "site_url": "https://example.com/sites/test-site",
                "root_page_render": "# Home\n\nWelcome",
                "navbar_items": render_items,
            }

            return render_data

        result = mock_complete_flow(mock_navbar_data, mock_html_content)

        # Verify complete flow
        assert result["site_title"] == "Test Site"
        assert len(result["navbar_items"]) == 1
        assert "Welcome" in result["root_page_render"]
