import asyncio
import re
import signal
import sys
from typing import List, Dict, Any, Optional, Set
import aiohttp
import orjson 
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm.asyncio import tqdm
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.parse import urlparse
import json
import os

from sub2md.Cache import Cache
from sub2md import Generator
from sub2md.utils.Exceptions import (
    NetworkError, ContentError, 
    FileSystemError, ConfigurationError,
    ValidationError
)
from sub2md.utils.Logger import Logger
from sub2md.utils.Config import (
    NETWORK, FILE_SYSTEM, PROCESSING,
    CONTENT, OUTPUT, URL
)

class SubstackScraper:
    """
    An optimized Substack scraper that uses concurrent processing and batch operations
    for better performance. Combines functionality from base, async, and optimized scrapers.
    """
    
    def __init__(
        self, 
        base_substack_url: str, 
        output_dir: str = "output", 
        debug: bool = False, 
        output_mode: str = OUTPUT['DEFAULT_MODE']
    ):
        """
        Initialize the scraper.
        
        Args:
            base_substack_url (str): The base URL of the Substack blog
            output_dir (str): Base directory for all outputs (default: "output")
            debug (bool): Enable debug mode
            output_mode (str): Output format ('both', 'md', or 'html')
            
        Raises:
            ValidationError: If input parameters are invalid
            ConfigurationError: If initialization fails
        """
        # Input validation
        if not base_substack_url or not isinstance(base_substack_url, str):
            raise ValidationError("base_substack_url must be a non-empty string")
        if not output_dir or not isinstance(output_dir, str):
            raise ValidationError("output_dir must be a non-empty string")
        if output_mode not in OUTPUT['VALID_MODES']:
            raise ValidationError(f"output_mode must be one of: {', '.join(OUTPUT['VALID_MODES'])}")
            
        self.base_substack_url = base_substack_url.rstrip('/')
        # Convert to Path object and resolve to absolute path
        self.output_dir = Path(output_dir).resolve()
        self.md_save_dir = self.output_dir / "substack_md_files"
        self.html_save_dir = self.output_dir / "substack_html_pages"
        self.cache_dir = self.output_dir / "cache"
        self.data_dir = self.output_dir / "data"
        self.debug = debug
        self.output_mode = output_mode
        
        # Initialize logger
        self.logger = Logger(debug=debug, log_file=str(self.output_dir / FILE_SYSTEM['DEFAULT_LOG_FILE']))
        
        # Initialize cache with the correct directory
        self.cache = Cache(cache_dir=str(self.cache_dir))
        
        # Create output directories
        try:
            self._create_directories()
        except Exception as e:
            raise FileSystemError(f"Failed to create output directories: {e}")
        
        # Initialize session
        self.session = None
        self.semaphore = None
        
        # Basic configuration
        self.writer_name = self._extract_main_part(base_substack_url)
        self.keywords = CONTENT['EXCLUDED_KEYWORDS']
        
        # Concurrency settings
        self.thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count() * PROCESSING['THREAD_POOL_MULTIPLIER'])
        self.file_io_semaphore = asyncio.Semaphore(PROCESSING['FILE_IO_SEMAPHORE_LIMIT'])
        self.cache_lock = threading.Lock()
        
        # Processing state
        self.processing_queue = asyncio.Queue()
        self.batch_queue = asyncio.Queue()
        self.processed_urls: Set[str] = set()
        self.results: List[Dict[str, Any]] = []
        self.batch_size = PROCESSING['BATCH_SIZE']
        
        # Initialize post_urls as empty list - will be populated in scrape_posts
        self.post_urls = []

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        try:
            # Create base output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            self.md_save_dir.mkdir(parents=True, exist_ok=True)
            self.html_save_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            if self.debug:
                self.logger.info(f"Created directory structure in: {self.output_dir}")
        except Exception as e:
            raise FileSystemError(f"Failed to create directories: {str(e)}")

    def _validate_path(self, path: Path) -> None:
        """Validate that a path is within the output directory."""
        try:
            path = path.resolve()
            if not str(path).startswith(str(self.output_dir)):
                raise ValidationError(f"Path {path} is outside the output directory")
        except Exception as e:
            raise ValidationError(f"Invalid path: {str(e)}")

    @staticmethod
    def _extract_main_part(url: str) -> str:
        """Extract the main part of the domain from a URL."""
        try:
            parts = urlparse(url).netloc.split('.')
            if not parts:
                raise ValidationError("Invalid URL format")
            middle_index = len(parts) // 2
            return parts[middle_index]
        except Exception as e:
            raise ValidationError(f"Failed to extract main part from URL: {str(e)}")

    async def init_session(self) -> None:
        """Initialize an optimized aiohttp session with high concurrency settings."""
        try:
            if not self.session:
                connector = aiohttp.TCPConnector(
                    limit=NETWORK['MAX_CONNECTIONS'],
                    ttl_dns_cache=NETWORK['DNS_CACHE_TTL'],
                    force_close=False,
                    enable_cleanup_closed=True,
                    ssl=False,
                    use_dns_cache=True,
                    keepalive_timeout=NETWORK['KEEPALIVE_TIMEOUT']
                )
                self.session = aiohttp.ClientSession(
                    headers={'User-Agent': NETWORK['USER_AGENT']},
                    timeout=aiohttp.ClientTimeout(
                        total=NETWORK['REQUEST_TIMEOUT'],
                        connect=NETWORK['CONNECT_TIMEOUT'],
                        sock_read=NETWORK['SOCK_READ_TIMEOUT']
                    ),
                    connector=connector,
                    json_serialize=orjson.dumps
                )
            self.semaphore = asyncio.Semaphore(NETWORK['MAX_CONCURRENT_REQUESTS'])
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize session: {str(e)}")

    async def close_session(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()

    def signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        self.logger.info("\nGracefully shutting down...")
        asyncio.create_task(self.close_session())
        sys.exit(0)

    async def get_all_post_urls(self) -> List[str]:
        """Get all post URLs from the substack."""
        if not self.session:
            await self.init_session()
            
        urls = await self._fetch_urls_from_sitemap()
        if not urls:
            self.logger.debug("Sitemap not available, falling back to feed.xml...")
            urls = await self._fetch_urls_from_feed()
            if urls:
                self.logger.info(f"Found {len(urls)} posts in feed.xml")
            else:
                self.logger.info("No posts found in feed.xml")
        else:
            self.logger.info(f"Found {len(urls)} posts in sitemap.xml")
        return self._filter_urls(urls, self.keywords)

    async def _fetch_urls_from_sitemap(self) -> List[str]:
        """Fetch URLs from sitemap."""
        try:
            sitemap_url = f"{self.base_substack_url}{URL['SITEMAP_PATH']}"
            async with self.session.get(sitemap_url) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'xml')
                    urls = [loc.text for loc in soup.find_all('loc')]
                    return [url for url in urls if URL['POST_PATH_PREFIX'] in url]
                return []
        except Exception as e:
            self.logger.warning(f"Failed to fetch sitemap: {e}")
            return []

    async def _fetch_urls_from_feed(self) -> List[str]:
        """Fetch URLs from feed."""
        try:
            feed_url = f"{self.base_substack_url}{URL['FEED_PATH']}"
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'xml')
                    return [link.text for link in soup.find_all('link')]
                return []
        except Exception as e:
            self.logger.warning(f"Failed to fetch feed: {e}")
            return []

    @staticmethod
    def _filter_urls(urls: List[str], keywords: List[str]) -> List[str]:
        """Filter out URLs containing certain keywords."""
        return [url for url in urls if all(keyword not in url for keyword in keywords)]

    async def process_url_batch(self, urls: List[str], pbar: tqdm) -> List[Dict[str, Any]]:
        """
        Process a list of URLs in batches for better performance.
        
        Args:
            urls: List of URLs to process
            pbar: Progress bar for tracking completion
            
        Returns:
            List of processed results
        """
        # Process URLs sequentially
        for url in urls:
            try:
                result = await self._process_single_url(url, pbar)
                if isinstance(result, dict):
                    self.results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}")
            finally:
                pbar.update(1)
            
        return self.results

    async def _process_single_url(self, url: str, pbar: Optional[tqdm] = None) -> Optional[Dict[str, Any]]:
        """
        Process a single URL with caching and error handling.
        
        Args:
            url: The URL to process
            pbar: Progress bar for tracking completion (not used with tqdm.asyncio)
            
        Returns:
            Dictionary containing processed data or None if processing failed
        """
        if url in self.processed_urls:
            return None
            
        try:
            self.logger.debug(f"[DEBUG] Processing post: {url}")
            
            async with self.semaphore:
                # Try cache first
                cached_soup = self.cache.get_cached_soup(url)
                if cached_soup:
                    self.logger.debug(f"Using cached content for {url}")
                    soup = cached_soup
                else:
                    self.logger.debug(f"Fetching content for {url}")
                    async with self.session.get(url) as response:
                        if response.status != 200:
                            raise NetworkError(f"Failed to fetch {url}: {response.status}")
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        self.cache.save_cached_soup(url, soup)
                
                # Extract post data
                post_data = self.extract_post_data(soup)
                
                # Save files
                if self.output_mode in ['both', 'md']:
                    self.save_markdown(post_data)
                if self.output_mode in ['both', 'html']:
                    self.save_html(post_data)
                
                self.logger.debug(f"[DEBUG] Successfully processed: {post_data['title']}")
                return post_data
                
        except NetworkError as e:
            if self.debug:
                self.logger.debug(f"[DEBUG] {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
            raise

    def extract_post_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract post data from BeautifulSoup object.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            Dict[str, Any]: Extracted post data
            
        Raises:
            ContentError: If content processing fails
        """
        try:
            content_div = self._find_content_div(soup)
            if not content_div:
                raise ContentError("Could not find content div")
            
            title = self._extract_title(soup)
            subtitle = self._extract_subtitle(content_div)
            date = self._extract_date(soup)
            like_count = self._extract_like_count(soup)
            is_paid = self._check_if_paid(soup)
            
            # Clean content
            self._clean_content(content_div)
            
            return {
                'title': title,
                'subtitle': subtitle,
                'date': date,
                'like_count': like_count,
                'is_paid': is_paid,
                'content': str(content_div)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting post data: {e}")
            raise ContentError(f"Failed to extract post data: {e}")

    def _find_content_div(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the main content div."""
        for class_name in CONTENT['CONTENT_DIV_CLASSES']:
            content_div = soup.find('div', class_=class_name)
            if content_div:
                return content_div
        raise ContentError("Could not find main content div")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title."""
        title_elem = soup.find(CONTENT['TITLE_TAG'])
        return title_elem.text.strip() if title_elem else "Untitled"

    def _extract_subtitle(self, content_div: BeautifulSoup) -> str:
        """Extract the subtitle."""
        subtitle_elem = content_div.find(CONTENT['SUBTITLE_TAG'])
        return subtitle_elem.text.strip() if subtitle_elem else ""

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract the date."""
        date_elem = soup.find(CONTENT['DATE_TAG'])
        return date_elem.text.strip() if date_elem else ""

    def _extract_like_count(self, soup: BeautifulSoup) -> int:
        """Extract the like count."""
        like_elem = soup.find('span', class_=CONTENT['LIKE_COUNT_CLASS'])
        if like_elem:
            try:
                return int(like_elem.text.strip())
            except ValueError:
                return 0
        return 0

    def _check_if_paid(self, soup: BeautifulSoup) -> bool:
        """Check if the post is paid content."""
        return bool(soup.find('div', class_=CONTENT['PAID_CONTENT_CLASS']))

    def _clean_content(self, content_div: BeautifulSoup) -> None:
        """Clean the content div."""
        # Remove unwanted elements
        for elem in content_div.find_all(CONTENT['REMOVE_ELEMENTS']):
            elem.decompose()
        
        # Remove empty paragraphs
        for p in content_div.find_all('p'):
            if not p.text.strip():
                p.decompose()

    def save_markdown(self, post_data: Dict[str, Any]) -> None:
        """
        Save post as Markdown.
        
        Args:
            post_data (Dict[str, Any]): Post data to save
            
        Raises:
            FileSystemError: If file operations fail
            ValidationError: If path is invalid
        """
        try:
            # Create author subdirectory if it doesn't exist
            author_dir = self.md_save_dir / self.writer_name
            author_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate the path is within output directory
            self._validate_path(author_dir)
            
            filename = f"{post_data['date']}_{post_data['title']}{OUTPUT['MARKDOWN_EXTENSION']}"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            filepath = author_dir / filename
            
            with open(filepath, 'w', encoding=FILE_SYSTEM['ENCODING']) as f:
                f.write(f"# {post_data['title']}\n\n")
                if post_data['subtitle']:
                    f.write(f"## {post_data['subtitle']}\n\n")
                f.write(f"Date: {post_data['date']}\n")
                f.write(f"Likes: {post_data['like_count']}\n")
                f.write(f"Paid: {post_data['is_paid']}\n\n")
                f.write(post_data['content'])
            
            self.logger.debug(f"Saved Markdown to {filepath}")
            
            # Update post data with file link
            post_data['file_link'] = str(Path('substack_md_files') / self.writer_name / filename)
            
        except Exception as e:
            self.logger.error(f"Error saving Markdown: {e}")
            raise FileSystemError(f"Failed to save Markdown: {e}")

    def save_html(self, post_data: Dict[str, Any]) -> None:
        """
        Save post as HTML.
        
        Args:
            post_data (Dict[str, Any]): Post data to save
            
        Raises:
            FileSystemError: If file operations fail
            ValidationError: If path is invalid
        """
        try:
            # Create author subdirectory if it doesn't exist
            author_dir = self.html_save_dir / self.writer_name
            author_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate the path is within output directory
            self._validate_path(author_dir)
            
            filename = f"{post_data['date']}_{post_data['title']}{OUTPUT['HTML_EXTENSION']}"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            filepath = author_dir / filename
            
            with open(filepath, 'w', encoding=FILE_SYSTEM['ENCODING']) as f:
                f.write(f"<!DOCTYPE html>\n<html>\n<head>\n")
                f.write(f"<title>{post_data['title']}</title>\n")
                f.write(f"</head>\n<body>\n")
                f.write(f"<h1>{post_data['title']}</h1>\n")
                if post_data['subtitle']:
                    f.write(f"<h2>{post_data['subtitle']}</h2>\n")
                f.write(f"<p>Date: {post_data['date']}</p>\n")
                f.write(f"<p>Likes: {post_data['like_count']}</p>\n")
                f.write(f"<p>Paid: {post_data['is_paid']}</p>\n")
                f.write(post_data['content'])
                f.write(f"\n</body>\n</html>")
            
            self.logger.debug(f"Saved HTML to {filepath}")
            
            # Update post data with HTML link
            post_data['html_link'] = str(Path('substack_html_pages') / self.writer_name / filename)
            
        except Exception as e:
            self.logger.error(f"Error saving HTML: {e}")
            raise FileSystemError(f"Failed to save HTML: {e}")

    async def scrape_posts(self, num_posts_to_scrape: int = 0) -> None:
        """Main method to scrape posts."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Initialize session and get post URLs
        await self.init_session()
        self.post_urls = await self.get_all_post_urls()
        
        # If num_posts_to_scrape is 0, use all posts
        # Otherwise, limit to the specified number
        urls_to_process = self.post_urls if num_posts_to_scrape == 0 else self.post_urls[:num_posts_to_scrape]
        
        if not urls_to_process:
            self.logger.info("No posts found to scrape.")
            return
            
        self.logger.info(f"Found {len(self.post_urls)} total posts. Scraping {len(urls_to_process)} posts...")
        
        try:
            essays_data = []
            # Create tasks for all URLs
            tasks = [self._process_single_url(url, None) for url in urls_to_process]
            
            # Create progress bar
            pbar = tqdm(
                total=len(urls_to_process),
                desc="🌐 Scraping posts",
                unit="post",
                bar_format="{desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt} posts [{elapsed}<{remaining}, {rate_fmt}]",
                ncols=100,
                position=0,
                leave=True
            )
            
            # Process tasks as they complete
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if isinstance(result, dict):
                    essays_data.append(result)
                pbar.update(1)
            
            pbar.close()
            self.save_essays_data_to_json(essays_data=essays_data)
            Generator.generate(self.writer_name, self.output_dir)
        finally:
            await self.close_session()

    def save_essays_data_to_json(self, essays_data: list) -> None:
        """Save essays data to JSON file."""
        try:
            json_path = self.data_dir / f'{self.writer_name}.json'
            
            # Validate the path is within output directory
            self._validate_path(json_path)
            
            existing_data = []
            
            # Try to read existing data, but handle corrupted/empty files
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding=FILE_SYSTEM['ENCODING']) as file:
                        existing_data = json.load(file)
                except json.JSONDecodeError:
                    self.logger.warning(f"Warning: Corrupted JSON file at {json_path}, starting fresh")
                    existing_data = []
                except Exception as e:
                    raise FileSystemError(f"Error reading JSON file: {str(e)}")
                    
            # Merge new data with existing data
            essays_data = existing_data + [data for data in essays_data if data not in existing_data]
            
            # Save the combined data
            with open(json_path, 'w', encoding=FILE_SYSTEM['ENCODING']) as f:
                json.dump(essays_data, f, ensure_ascii=False, indent=OUTPUT['JSON_INDENT'])
        except Exception as e:
            raise FileSystemError(f"Error saving essays data: {str(e)}")

    def __del__(self):
        """Cleanup thread pool on deletion."""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False) 