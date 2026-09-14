from app.domain.entities import RetrievedSource
from app.services.source_preprocessor import SourcePreprocessor


def make_source(external_id: str, excerpt: str, upvotes: int = 0) -> RetrievedSource:
    return RetrievedSource(
        external_id=external_id,
        provider="demo",
        title=f"Title {external_id}",
        author_name="Demo Author",
        source_url=f"https://example.com/{external_id}",
        excerpt=excerpt,
        engagement={"upvotes": upvotes},
    )


def test_prepare_filters_duplicates_cleans_and_numbers_sources():
    sources = [
        make_source("one", "<p>" + "Useful content " * 10 + "</p>", 10),
        make_source("one", "Duplicate content " * 10, 100),
        make_source("two", "Second useful source " * 10, 20),
        make_source("short", "too short"),
    ]

    result = SourcePreprocessor().prepare(sources, max_items=10, max_chars=80)

    assert [item.source_key for item in result] == ["S1", "S2"]
    assert len({item.external_id for item in result}) == 2
    assert all("<p>" not in item.excerpt for item in result)
    assert all(len(item.excerpt) <= 80 for item in result)

