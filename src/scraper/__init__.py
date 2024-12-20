"""University of Bristol SharePoint Scraper.

This package provides tools for scraping and converting University of Bristol
SharePoint sites into structured markdown documentation. The scraper extracts
navigation structures and page content to create organized site maps and
documentation.

Main modules:
- navbar_parser: Extract navigation structure from SharePoint HTML
- navbar_helpers: Process and flatten navigation data
- general_parser: Extract content elements (headers, links) from pages
- markdown_converter: Convert HTML elements to markdown format
- page_render: Combine content and navigation into formatted pages
- config: Configuration constants and settings

Data types:
- data_types.navbar: Navigation item structures
- data_types.render_data: Page rendering data structures
"""
