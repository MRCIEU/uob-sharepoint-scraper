"""Test data type definitions."""

from scraper.data_types.navbar import NavbarItem, NavbarItemProcessed
from scraper.data_types.render_data import RenderNavbarItem, RenderData


def test_navbar_item_structure():
    """Test that NavbarItem has expected structure."""
    # Create a sample NavbarItem
    item: NavbarItem = {
        "title": "Test Page",
        "url": "/test",
        "is_external": False,
        "base_level": 1,
        "children": [],
    }

    assert item["title"] == "Test Page"
    assert item["url"] == "/test"
    assert item["is_external"] is False
    assert item["base_level"] == 1
    assert len(item["children"]) == 0


def test_navbar_item_processed_structure():
    """Test that NavbarItemProcessed has expected structure."""
    item: NavbarItemProcessed = {
        "title": "Test Page",
        "slug": "test-page",
        "base_url": "/test",
        "url": "https://example.com/test",
        "is_external": False,
        "base_level": 1,
        "scrape": True,
    }

    assert item["title"] == "Test Page"
    assert item["slug"] == "test-page"
    assert item["scrape"] is True


def test_render_navbar_item_structure():
    """Test that RenderNavbarItem has expected structure."""
    item: RenderNavbarItem = {
        "title": "Test Page",
        "slug": "test-page",
        "url": "https://example.com/test",
        "page_render": None,
        "level": 2,
    }

    assert item["title"] == "Test Page"
    assert item["level"] == 2
    assert item["page_render"] is None


def test_render_data_structure():
    """Test that RenderData has expected structure."""
    data: RenderData = {
        "site_title": "Test Site",
        "site_slug": "test-site",
        "site_url": "https://example.com/sites/test-site",
        "root_page_render": None,
        "navbar_items": [],
    }

    assert data["site_title"] == "Test Site"
    assert data["site_slug"] == "test-site"
    assert len(data["navbar_items"]) == 0


def test_optional_fields():
    """Test that optional fields can be None."""
    # Test NavbarItem with None values
    item: NavbarItem = {
        "title": "Test",
        "url": None,
        "is_external": None,
        "base_level": 0,
        "children": [],
    }
    assert item["url"] is None
    assert item["is_external"] is None

    # Test RenderNavbarItem with None values
    render_item: RenderNavbarItem = {
        "title": "Test",
        "slug": "test",
        "url": None,
        "page_render": None,
        "level": 1,
    }
    assert render_item["url"] is None
    assert render_item["page_render"] is None
