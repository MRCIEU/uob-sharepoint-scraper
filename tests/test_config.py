"""Test configuration module functionality."""

from scraper import config


def test_site_root_constant():
    """Test that SITE_ROOT constant is properly defined."""
    assert config.SITE_ROOT == "https://uob.sharepoint.com"
    assert isinstance(config.SITE_ROOT, str)
    assert config.SITE_ROOT.startswith("https://")


def test_site_root_format():
    """Test that SITE_ROOT follows expected URL format."""
    assert config.SITE_ROOT.endswith(".sharepoint.com")
    assert "uob" in config.SITE_ROOT
