# Scraper for Microsoft SharePoint sites in University of Bristol

This tool extracts and converts University of Bristol SharePoint sites into structured markdown documentation. The system works by extracting navigation structure from SharePoint pages and generating comprehensive site maps in markdown format.

The scraper follows a pipeline architecture where data flows through specialized modules: navigation extraction → content scraping → markdown generation → document assembly. For detailed technical information, see @DEV.md.

This software is co-developed with AI agents using opencode.

## Usage

### Batch Processing (Recommended)

The `all-sites.py` script processes all sites listed in `SITES.txt` automatically:

**Basic usage:**

```bash
just all-sites
# or directly:
uv run scripts/all-sites.py
```

**Options:**

- `--dry-run, -n` - Show what would be done without executing
- `--force all` - Force processing of all sites (both scrape and generate)
- `--force scrape` - Force only the scraping step
- `--force generate` - Force only the sitemap generation step

By default, the script only processes sites that don't have existing data in the output directory.

### Individual Site Processing

#### 1. Scraping SharePoint Sites

The `scrape-site.py` script automates the process of extracting content from SharePoint sites using Playwright.

**Basic usage:**

```bash
uv run scripts/scrape-site.py --site <SITE_SLUG>
```

**Options:**

- `--site SLUG` - SharePoint site slug (default: "integrative-epidemiology")
- `--dry-run, -n` - Show what would be done without executing
- `--force` - Re-scrape pages even if they already exist

**Output structure:**

```
output/site-data/<site-slug>/
├── index.html              # Main site page
├── navbar_links.json       # Navigation structure data
└── pages/                  # Individual scraped pages
    ├── page1.aspx.html
    ├── page2.aspx.html
    └── ...
```

#### 2. Generating Sitemaps

The `generate-sitemap.py` script processes scraped data and creates markdown documentation.

**Basic usage:**

```bash
uv run scripts/generate-sitemap.py --site <SITE_SLUG>
```

**Options:**

- `--site SLUG` - SharePoint site slug (required)
- `--dry-run, -n` - Show what would be done without executing

**Output:**

- Creates `output/<site-slug>.md` with complete site documentation

## Site Configuration

Sites to be processed are listed in `SITES.txt`, one site slug per line.

## Authentication

The scraper uses Playwright browser automation to handle University of Bristol SharePoint authentication. Interactive authentication is handled automatically during the first site access.

## Other details

- For setting up the project and technical details, refer to @DEV.md
- For todo list, refer to @TODO.org
