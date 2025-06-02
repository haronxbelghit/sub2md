import hashlib
import threading
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import aiofiles 
from pathlib import Path

class Cache:
    """
    A high-performance caching system that supports file-based caching
    with memory mapping for optimal performance.
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the cache system.
        
        Args:
            cache_dir: Directory for file-based cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        # Thread safety
        self._lock = threading.Lock()
        self._mmap_cache: Dict[str, Any] = {}
            
    def _get_cache_key(self, url: str) -> str:
        """
        Generate a cache key from a URL.
        
        Args:
            url: The URL to generate a key for
            
        Returns:
            str: MD5 hash of the URL
        """
        return hashlib.md5(url.encode()).hexdigest()
        
    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the full path for a cache file.
        
        Args:
            cache_key: The cache key
            
        Returns:
            Path: Full path to the cache file
        """
        return self.cache_dir / f"{cache_key}.cache"
        
    def get_cached_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get cached BeautifulSoup object for URL.
        
        Args:
            url: The URL to get cached content for
            
        Returns:
            Optional[BeautifulSoup]: Cached BeautifulSoup object or None if not found
        """
        cache_key = self._get_cache_key(url)
                
        # File cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    return BeautifulSoup(html_content, "lxml")
            except Exception as e:
                print(f"File cache read error: {e}")
                
        return None
        
    def save_cached_soup(self, url: str, soup: BeautifulSoup) -> None:
        """
        Save BeautifulSoup object to cache.
        
        Args:
            url: The URL to cache
            soup: BeautifulSoup object to cache
        """
        cache_key = self._get_cache_key(url)
        html_content = str(soup)
                
        # File cache
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            print(f"File cache write error: {e}")
            
    async def save_cached_soup_async(self, url: str, soup: BeautifulSoup) -> None:
        """
        Asynchronously save BeautifulSoup object to cache.
        
        Args:
            url: The URL to cache
            soup: BeautifulSoup object to cache
        """
        cache_key = self._get_cache_key(url)
        html_content = str(soup)
                
        # File cache
        cache_path = self._get_cache_path(cache_key)
        try:
            async with aiofiles.open(cache_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)
        except Exception as e:
            print(f"File async cache write error: {e}")
            
    def clear_cache(self) -> None:
        """Clear all cached data from file system."""
        # Clear file cache
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    print(f"Error deleting cache file {cache_file}: {e}")
        except Exception as e:
            print(f"File cache clear error: {e}")
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dict containing cache statistics
        """
        stats = {
            "file_cache_count": 0,
            "file_cache_size": 0
        }
        
        # Get file cache stats
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                stats["file_cache_count"] += 1
                stats["file_cache_size"] += cache_file.stat().st_size
        except Exception:
            pass
            
        return stats 