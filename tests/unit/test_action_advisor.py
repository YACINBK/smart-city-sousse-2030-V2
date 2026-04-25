from ai.action_advisor import ActionAdvisor


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def complete(self, prompt: str, max_tokens: int = 1500) -> str:
        return self._responses.pop(0)


class _FakeContext:
    def quick_stats(self) -> dict:
        return {
            "hors_service_count": 8,
            "pending_interventions": 41,
            "critical_alerts": 0,
            "critical_zones": 4,
            "vehicles_breakdown": 6,
        }


def test_parse_json_object_accepts_code_fences():
    raw = """```json
{
  "actions": [],
  "resume": "ok",
  "niveau_urgence": "VERT"
}
```"""

    data = ActionAdvisor._parse_json_object(raw)

    assert data["niveau_urgence"] == "VERT"
    assert data["resume"] == "ok"


def test_get_priority_actions_retries_after_truncated_response():
    truncated = """```json
{
  "actions": [
    {
      "priorite": 1,
      "titre": "Action incomplete"
"""
    valid = """```json
{
  "actions": [
    {
      "priorite": 2,
      "titre": "Deuxieme action",
      "description": "Desc",
      "justification": "Pourquoi",
      "responsable": "gestionnaire",
      "delai_heures": 4,
      "impact": "Impact",
      "indicateur_succes": "Succes"
    },
    {
      "priorite": 1,
      "titre": "Premiere action",
      "description": "Desc",
      "justification": "Pourquoi",
      "responsable": "technicien",
      "delai_heures": 2,
      "impact": "Impact",
      "indicateur_succes": "Succes"
    }
  ],
  "resume": "Resume propre",
  "niveau_urgence": "ORANGE"
}
```"""

    advisor = ActionAdvisor(client=_FakeClient([truncated, valid]))
    advisor._ctx = _FakeContext()

    data = advisor.get_priority_actions()

    assert data["niveau_urgence"] == "ORANGE"
    assert [item["priorite"] for item in data["actions"]] == [1, 2]
    assert data["resume"] == "Resume propre"
