"""Test navbar parser functionality with mock SharePoint HTML."""

from scraper import navbar_parser


def test_extract_navbar_item_basic():
    """Test extracting basic navbar item from SharePoint data."""
    raw_item = {
        "Id": 1,
        "Title": "Home",
        "Url": "/sites/test/",
        "IsExternal": False,
        "Children": [],
    }

    result = navbar_parser.extract_navbar_item(raw_item, base_level=0)

    assert result is not None
    assert result["title"] == "Home"
    assert result["url"] == "/sites/test/"
    assert result["is_external"] is False
    assert result["base_level"] == 0
    assert len(result["children"]) == 0


def test_extract_navbar_item_with_children():
    """Test extracting navbar item with nested children."""
    raw_item = {
        "Id": 1,
        "Title": "Parent",
        "Url": "/parent",
        "IsExternal": False,
        "Children": [
            {
                "Id": 2,
                "Title": "Child",
                "Url": "/child",
                "IsExternal": False,
                "Children": [],
            }
        ],
    }

    result = navbar_parser.extract_navbar_item(raw_item, base_level=0)

    assert result is not None
    assert result["title"] == "Parent"
    assert len(result["children"]) == 1
    assert result["children"][0]["title"] == "Child"
    assert result["children"][0]["base_level"] == 1


def test_extract_navbar_item_none_title():
    """Test that items with None title return None."""
    raw_item = {
        "Id": 1,
        "Title": None,
        "Url": "/test",
        "IsExternal": False,
        "Children": [],
    }

    result = navbar_parser.extract_navbar_item(raw_item)
    assert result is None


def test_get_navbar_items_filters_none():
    """Test that get_navbar_items filters out None results."""
    raw_data = [
        {
            "Id": 1,
            "Title": "Valid Item",
            "Url": "/valid",
            "IsExternal": False,
            "Children": [],
        },
        {
            "Id": 2,
            "Title": None,  # This will be filtered out
            "Url": "/invalid",
            "IsExternal": False,
            "Children": [],
        },
    ]

    result = navbar_parser.get_navbar_items(raw_data)

    assert len(result) == 1
    assert result[0]["title"] == "Valid Item"


def test_get_quick_launch_data_structure():
    """Test that we can identify the structure needed for quick launch data.

    This is more of a documentation test showing what structure is expected.
    """
    # This is the type of JavaScript data we expect to find in SharePoint pages
    expected_navigation_structure = {
        "navigationInfo": {
            "quickLaunch": [
                {
                    "Id": 1,
                    "Title": "Home",
                    "Url": "/sites/test/",
                    "IsExternal": False,
                    "Children": [],
                }
            ]
        }
    }

    # Verify the structure is as expected
    quick_launch = expected_navigation_structure["navigationInfo"][
        "quickLaunch"
    ]
    assert isinstance(quick_launch, list)
    assert len(quick_launch) > 0
    assert "Title" in quick_launch[0]
    assert "Url" in quick_launch[0]
