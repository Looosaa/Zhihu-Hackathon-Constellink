from app.providers.content.zhihu import ZhihuContentProvider


def test_normalizes_current_official_zhihu_shape():
    payload = {
        "Code": 0,
        "Message": "success",
        "Data": {
            "HasMore": False,
            "Items": [
                {
                    "Title": "测试问题",
                    "ContentType": "Answer",
                    "ContentID": "123",
                    "AuthorName": "测试作者",
                    "AuthorBadgeText": "专业回答者",
                    "ContentText": "这是用于契约测试的合成内容。",
                    "Url": "https://www.zhihu.com/question/1/answer/123",
                    "CommentCount": 4,
                    "VoteUpCount": 20,
                    "AuthorityLevel": "L3",
                    "RankingScore": 0.95,
                }
            ],
        },
    }

    provider = ZhihuContentProvider(
        base_url="https://developer.zhihu.com/api/v1",
        access_secret="test-secret",
    )
    items = provider._normalize_payload(payload, limit=8)

    assert len(items) == 1
    assert items[0].external_id == "123"
    assert items[0].provider.value == "zhihu"
    assert items[0].title == "测试问题"
    assert items[0].author_name == "测试作者"
    assert items[0].engagement == {"upvotes": 20, "comments": 4}
