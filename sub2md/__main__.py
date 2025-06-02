import argparse
import asyncio
import time
import os
from pathlib import Path
from sub2md.Scraper import SubstackScraper

# Default configuration
USE_PREMIUM: bool = False
BASE_SUBSTACK_URL: str = ""
NUM_POSTS_TO_SCRAPE: int = 0

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Scrape Substack posts and convert to Markdown')
    parser.add_argument('-u', '--url', help='Substack URL to scrape')
    parser.add_argument('-n', '--number', type=int, default=10, help='Number of posts to scrape (0 for all)')
    parser.add_argument('-d', '--directory', help='Base output directory (default: ./output)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with timing information')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-om', '--only-md', action='store_true', help='Save only Markdown files')
    group.add_argument('-oh', '--only-html', action='store_true', help='Save only HTML files')
    return parser.parse_args()

def get_output_dir(custom_dir: str = None) -> Path:
    """Get the output directory path.
    If custom_dir is provided, use it. Otherwise, create an 'output' directory in the current working directory.
    """
    if custom_dir:
        return Path(custom_dir)
    return Path.cwd() / "output"

def main():
    """Main entry point."""
    args = parse_args()
    start_time = time.time()

    output_mode = 'both'
    if args.only_md:
        output_mode = 'md'
    elif args.only_html:
        output_mode = 'html'

    # Get output directory
    output_dir = get_output_dir(args.directory)
    print(f"Output will be saved to: {output_dir}")

    if args.url:
        scraper = SubstackScraper(
            base_substack_url=args.url,
            output_dir=str(output_dir),
            debug=args.debug,
            output_mode=output_mode
        )
        asyncio.run(scraper.scrape_posts(args.number))
    else:  # Use the hardcoded values
        scraper = SubstackScraper(
            base_substack_url=BASE_SUBSTACK_URL,
            output_dir=str(output_dir),
            debug=args.debug,
            output_mode=output_mode
        )
        asyncio.run(scraper.scrape_posts(num_posts_to_scrape=NUM_POSTS_TO_SCRAPE))

    if args.debug:
        total_time = time.time() - start_time
        print(f"\nTotal execution time: {total_time:.2f} seconds")

if __name__ == '__main__':
    main() 