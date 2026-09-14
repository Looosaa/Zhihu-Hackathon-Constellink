from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

CLIENT_ID = "test-browser-1234567890"


def test_complete_offline_learning_flow():
    settings = Settings(
        repository_backend="memory",
        content_provider="demo",
        llm_backend="fake",
    )
    with TestClient(create_app(settings)) as client:
        created = client.post(
            "/api/spaces",
            json={
                "client_id": CLIENT_ID,
                "topic": "零基础学习机器学习，需要先系统学习数学吗？",
                "level": "beginner",
                "goal": "project",
                "daily_minutes": 15,
            },
        )
        assert created.status_code == 201, created.text
        space_id = created.json()["data"]["id"]

        analyzed = client.post(
            f"/api/spaces/{space_id}/analyze",
            json={"client_id": CLIENT_ID, "force": False},
        )
        assert analyzed.status_code == 200, analyzed.text
        body = analyzed.json()
        assert len(body["data"]["sources"]) >= 8
        assert len(body["data"]["analysis"]["concepts"]) >= 8
        assert body["meta"]["execution_mode"] == "demo"

        plan = client.post(
            f"/api/spaces/{space_id}/plan",
            json={"client_id": CLIENT_ID, "force": False},
        )
        assert plan.status_code == 200, plan.text
        assert len(plan.json()["data"]["days"]) == 7

        quiz = client.post(
            f"/api/spaces/{space_id}/quizzes",
            json={"client_id": CLIENT_ID, "concept_id": "evaluation"},
        )
        assert quiz.status_code == 201, quiz.text
        quiz_body = quiz.json()["data"]
        assert "reference_answer" not in quiz_body

        graded = client.post(
            f"/api/quizzes/{quiz_body['id']}/attempts",
            json={
                "client_id": CLIENT_ID,
                "answer": "训练集用来学习参数，测试集用来检查面对新数据的效果。",
            },
        )
        assert graded.status_code == 200, graded.text
        assert 0 <= graded.json()["data"]["score"] <= 100

        fetched = client.get(
            f"/api/spaces/{space_id}", params={"client_id": CLIENT_ID}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["data"]["space"]["status"] == "ready"
        assert fetched.json()["data"]["plan"] is not None

