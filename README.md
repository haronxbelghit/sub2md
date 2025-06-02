# Sub2Md

A Python package for scraping Substack posts and converting them to Markdown format.

## Installation

You can install the package directly from GitHub using pip:

```bash
pip install -e git+https://github.com/haronxbelghit/sub2md.git#egg=sub2md
```

## Usage

The package can be used both as a command-line tool and as a Python module.

### Command Line Usage

```bash

# Scrape a specific Substack URL
sub2md -u https://example.substack.com

# Specify number of posts to scrape
sub2md -u https://example.substack.com -n 5

# Save only Markdown files
sub2md -u https://example.substack.com -n 5 --only-md (-om)

# Save only HTML files
sub2md -u https://example.substack.com -n 5 --only-html (-oh)

# Specify custom output directory
sub2md  -u https://example.substack.com -n 5 -d /path/to/output

# Enable debug mode with timing information
sub2md -u https://example.substack.com -n 5 -om --debug
```

### Python Module Usage

```python
from sub2md import SubstackScraper

# Initialize the scraper
scraper = SubstackScraper(
    base_substack_url="https://example.substack.com",
    output_dir="./output",
    debug=False,
    output_mode='both'  # Options: 'both', 'md', 'html'
)

# Scrape posts
await scraper.scrape_posts(num_posts_to_scrape=10)  # 0 for all posts
```

## Features

- Scrape Substack posts and convert them to Markdown format
- Save both HTML and Markdown versions of posts
- Configurable output directory
- Debug mode with timing information
- Support for custom Substack URLs
- Control over number of posts to scrape

## Requirements

- Python 3.6+
- See `requirements.txt` for dependencies

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 