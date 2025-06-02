"""Configuration settings for the Substack scraper."""

# Network settings
NETWORK = {
    'MAX_CONCURRENT_REQUESTS': 5,
    'REQUEST_TIMEOUT': 30,
    'CONNECT_TIMEOUT': 10,
    'SOCK_READ_TIMEOUT': 10,
    'KEEPALIVE_TIMEOUT': 30,
    'DNS_CACHE_TTL': 300,
    'MAX_CONNECTIONS': 200,
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# File system settings
FILE_SYSTEM = {
    'DEFAULT_CACHE_DIR': 'cache',
    'DEFAULT_DATA_DIR': 'data',
    'DEFAULT_LOG_FILE': 'sub2md.log',
    'FILE_BUFFER_SIZE': 1024 * 1024,  # 1MB
    'ENCODING': 'utf-8'
}

# Processing settings
PROCESSING = {
    'BATCH_SIZE': 10,
    'MAX_WORKERS': 20,
    'THREAD_POOL_MULTIPLIER': 4,  # Number of threads per CPU core
    'FILE_IO_SEMAPHORE_LIMIT': 500
}

# Content settings
CONTENT = {
    'EXCLUDED_KEYWORDS': ['about', 'archive', 'podcast'],
    'CONTENT_DIV_CLASSES': ['body', 'post-content'],
    'TITLE_TAG': 'h1',
    'SUBTITLE_TAG': 'h2',
    'DATE_TAG': 'time',
    'LIKE_COUNT_CLASS': 'like-count',
    'PAID_CONTENT_CLASS': 'paid-content',
    'REMOVE_ELEMENTS': ['script', 'style', 'iframe']
}

# Output settings
OUTPUT = {
    'VALID_MODES': ['both', 'md', 'html'],
    'DEFAULT_MODE': 'both',
    'MARKDOWN_EXTENSION': '.md',
    'HTML_EXTENSION': '.html',
    'JSON_INDENT': 4
}

# URL settings
URL = {
    'SITEMAP_PATH': '/sitemap.xml',
    'FEED_PATH': '/feed',
    'POST_PATH_PREFIX': '/p/'
} 