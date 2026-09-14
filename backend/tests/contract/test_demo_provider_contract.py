import asyncio
from pathlib import Path

from app.providers.content.demo import DemoContentProvider


def test_demo_provider_contract():
    path = Path(__file__).resolve().parents[2] / "data" / "demo_sources.json"
    items = asyncio.run(DemoContentProvider(path).search("machine learning", 8))

    assert len(items) == 8
    assert len({item.external_id for item in items}) == len(items)
    assert all(item.title and item.author_name and item.excerpt for item in items)
    assert all(str(item.source_url).startswith("https://") for item in items)

