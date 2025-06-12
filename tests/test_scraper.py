import sys
from pathlib import Path
import types
import pytest

# Stub out optional dependencies so that the module can be imported
sys.modules.setdefault('aiohttp', types.SimpleNamespace(TCPConnector=None, ClientSession=None, ClientTimeout=None))
sys.modules.setdefault('orjson', types.SimpleNamespace(dumps=None))
sys.modules.setdefault('bs4', types.SimpleNamespace(BeautifulSoup=None))
sys.modules.setdefault('aiofiles', types.SimpleNamespace(open=lambda *a, **k: None))

tqdm_stub = types.ModuleType('tqdm')
tqdm_asyncio_stub = types.ModuleType('asyncio')
tqdm_asyncio_stub.tqdm = lambda *args, **kwargs: None
tqdm_stub.asyncio = tqdm_asyncio_stub
sys.modules.setdefault('tqdm', tqdm_stub)
sys.modules.setdefault('tqdm.asyncio', tqdm_asyncio_stub)

sys.path.append(str(Path(__file__).resolve().parents[1]))
from sub2md.Scraper import SubstackScraper

@pytest.mark.parametrize("url", [
    "https://example.substack.com",
    "https://blog.example.com",
    "https://example.com",
])
def test_extract_main_part(url):
    assert SubstackScraper._extract_main_part(url) == "example"
