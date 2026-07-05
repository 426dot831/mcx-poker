from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from mcx_poker.delivery.api import DeliveryError, create_app


def fixed_snapshot(**overrides: Any) -> dict[str, Any]:
    snapshot = {
        "table_id": "table-1",
        "status": "idle",
        "seat_count": 6,
        "seats": [
            {
                "seat_index": index,
                "player_id": None,
                "player_name": None,
                "controller_type": None,
                "stack": 0,
                "status": "empty",
            }
            for index in range(6)
        ],
        "button_seat_index": None,
        "current_hand_id": None,
    }
    snapshot.update(overrides)
    return snapshot


class FakeTableManager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.occupied = False
        self.duplicate_player = False
        self.business_error: str | None = None
        self.crash = False

    def initialize_table(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(("initialize_table", config))
        return fixed_snapshot()

    def seat_player(
        self,
        seat_index: int,
        player_name: str,
        controller_type: str,
        starting_stack: int,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "seat_player",
                {
                    "seat_index": seat_index,
                    "player_name": player_name,
                    "controller_type": controller_type,
                    "starting_stack": starting_stack,
                },
            )
        )
        if self.occupied:
            raise DeliveryError("seat_occupied", "seat is occupied")
        if self.duplicate_player:
            raise DeliveryError("player_already_seated", "player already seated")
        snapshot = fixed_snapshot()
        snapshot["seats"][seat_index].update(
            {
                "player_id": f"player-{seat_index}",
                "player_name": player_name,
                "controller_type": controller_type,
                "stack": starting_stack,
                "status": "seated",
            }
        )
        return snapshot

    def start_table(self, table_id: str) -> dict[str, Any]:
        self.calls.append(("start_table", table_id))
        return fixed_snapshot(table_id=table_id, status="running")

    def pause_table(self, table_id: str) -> dict[str, Any]:
        self.calls.append(("pause_table", table_id))
        return fixed_snapshot(table_id=table_id, status="paused")

    def resume_table(self, table_id: str) -> dict[str, Any]:
        self.calls.append(("resume_table", table_id))
        return fixed_snapshot(table_id=table_id, status="running")

    def reset_table(self, table_id: str) -> dict[str, Any]:
        self.calls.append(("reset_table", table_id))
        return fixed_snapshot(table_id=table_id, status="idle")

    def get_table(self, table_id: str) -> dict[str, Any]:
        self.calls.append(("get_table", table_id))
        if self.business_error:
            raise DeliveryError(self.business_error, "mapped business error")
        if self.crash:
            raise RuntimeError("traceback details should not leak")
        snapshot = fixed_snapshot(table_id=table_id)
        snapshot["seats"][0]["hole_cards"] = ["As", "Ah"]
        snapshot["adapter_hand_ref"] = {"pokerkit_object": "do-not-leak"}
        return snapshot


class FakeHumanController:
    def __init__(self) -> None:
        self.invalidated: list[str] = []
        self.paused: list[str] = []

    def invalidate_pending_actions(self, table_id: str) -> None:
        self.invalidated.append(table_id)

    def on_table_paused(self, table_id: str) -> None:
        self.paused.append(table_id)


def assert_error(response: Any, code: str) -> None:
    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert body["error"]["code"] == code


def test_api_t01_initialize_returns_fixed_six_seat_snapshot() -> None:
    manager = FakeTableManager()
    client = TestClient(create_app(manager))

    response = client.post("/api/table/initialize", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["error"] is None
    assert body["data"]["table_id"] == "table-1"
    assert len(body["data"]["seats"]) == 6
    assert manager.calls == [("initialize_table", {})]


def test_api_t02_invalid_seat_request_returns_invalid_request() -> None:
    manager = FakeTableManager()
    client = TestClient(create_app(manager))

    missing = client.post("/api/table/seats", json={"seat_index": 0})
    invalid = client.post(
        "/api/table/seats",
        json={
            "seat_index": 6,
            "player_name": "Ada",
            "controller_type": "human",
            "starting_stack": 100,
        },
    )

    assert missing.status_code == 400
    assert_error(missing, "invalid_request")
    assert invalid.status_code == 400
    assert_error(invalid, "invalid_request")


def test_api_t03_occupied_seat_returns_stable_error() -> None:
    manager = FakeTableManager()
    manager.occupied = True
    client = TestClient(create_app(manager))

    response = client.post(
        "/api/table/seats",
        json={
            "seat_index": 0,
            "player_name": "Ada",
            "controller_type": "human",
            "starting_stack": 100,
        },
    )

    assert response.status_code == 409
    assert_error(response, "seat_occupied")


def test_api_t04_duplicate_player_returns_stable_error() -> None:
    manager = FakeTableManager()
    manager.duplicate_player = True
    client = TestClient(create_app(manager))

    response = client.post(
        "/api/table/seats",
        json={
            "seat_index": 1,
            "player_name": "Ada",
            "controller_type": "human",
            "starting_stack": 100,
        },
    )

    assert response.status_code == 409
    assert_error(response, "player_already_seated")


def test_api_t05_unknown_controller_type_returns_stable_error() -> None:
    manager = FakeTableManager()
    client = TestClient(create_app(manager))

    response = client.post(
        "/api/table/seats",
        json={
            "seat_index": 0,
            "player_name": "Ada",
            "controller_type": "robot",
            "starting_stack": 100,
        },
    )

    assert response.status_code == 400
    assert_error(response, "unknown_controller_type")


def test_api_t06_control_commands_call_table_manager_methods() -> None:
    manager = FakeTableManager()
    human_controller = FakeHumanController()
    client = TestClient(create_app(manager, human_controller=human_controller))

    for command in ("start", "pause", "resume", "reset"):
        response = client.post(
            "/api/table/control",
            json={"table_id": "table-1", "command": command},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    assert manager.calls == [
        ("start_table", "table-1"),
        ("pause_table", "table-1"),
        ("resume_table", "table-1"),
        ("reset_table", "table-1"),
    ]
    assert human_controller.paused == ["table-1"]
    assert human_controller.invalidated == ["table-1"]


def test_api_t07_get_table_does_not_include_hidden_cards_or_pokerkit_objects() -> None:
    manager = FakeTableManager()
    client = TestClient(create_app(manager))

    response = client.get("/api/table/table-1")

    assert response.status_code == 200
    body_text = response.text
    assert "hole_cards" not in body_text
    assert "adapter_hand_ref" not in body_text
    assert "pokerkit" not in body_text.lower()


def test_api_t08_table_manager_business_errors_are_mapped() -> None:
    manager = FakeTableManager()
    manager.business_error = "table_not_initialized"
    client = TestClient(create_app(manager))

    response = client.get("/api/table/table-1")

    assert response.status_code == 404
    assert_error(response, "table_not_initialized")


def test_api_t09_unknown_exceptions_do_not_leak_tracebacks() -> None:
    manager = FakeTableManager()
    manager.crash = True
    client = TestClient(create_app(manager))

    response = client.get("/api/table/table-1")

    assert response.status_code == 500
    assert_error(response, "internal_error")
    body_text = response.text.lower()
    assert "runtimeerror" not in body_text
    assert "traceback" not in body_text
