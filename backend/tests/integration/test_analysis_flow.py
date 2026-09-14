from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.providers.llm.fake import FakeLLM

CLIENT_ID = "test-browser-1234567890"


class CountingFakeLLM(FakeLLM):
    def __init__(self):
        self.tasks: list[str] = []
        self.timeouts: list[float | None] = []

    async def generate_structured(self, **kwargs):
        self.tasks.append(kwargs["task_name"])
        self.timeouts.append(kwargs.get("timeout_seconds"))
        return await super().generate_structured(**kwargs)


def test_complete_offline_learning_flow():
    settings = Settings(
        repository_backend="memory",
        content_provider="demo",
        llm_backend="fake",
    )
    app = create_app(settings)
    counting_llm = CountingFakeLLM()
    app.state.container.llm = counting_llm
    app.state.container.analysis_orchestrator.llm = counting_llm
    app.state.container.plan_service.llm = counting_llm
    app.state.container.quiz_service.llm = counting_llm

    with TestClient(app) as client:
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
        assert analyzed.status_code == 202, analyzed.text
        body = analyzed.json()
        assert body["data"]["space_id"] == space_id
        assert body["data"]["status"] == "accepted"

        completed = client.get(
            f"/api/spaces/{space_id}", params={"client_id": CLIENT_ID}
        )
        assert completed.status_code == 200, completed.text
        completed_body = completed.json()
        assert len(completed_body["data"]["sources"]) >= 8
        assert len(completed_body["data"]["analysis"]["concepts"]) >= 8
        assert counting_llm.tasks == ["analyze_sources"]
        assert counting_llm.timeouts == [120]

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
