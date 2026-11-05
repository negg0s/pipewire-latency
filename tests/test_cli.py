import json

from pipewire_latency import cli
from pipewire_latency.state import PipeWireState


def _state() -> PipeWireState:
    return PipeWireState(quantum=64, rate=48000, source="test", driver="test-sink")


def test_measure_prints_latency(monkeypatch, capsys):
    monkeypatch.setattr(cli, "collect_state", _state)
    assert cli.main(["measure"]) == 0
    out = capsys.readouterr().out
    assert "1.333 ms" in out


def test_measure_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "collect_state", _state)
    assert cli.main(["measure", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["quantum"] == 64
    assert payload["rate"] == 48000
    assert payload["buffer_ms"] == 1.333


def test_measure_missing_state(monkeypatch, capsys):
    monkeypatch.setattr(cli, "collect_state", lambda: PipeWireState(warnings=("pw-dump missing",)))
    assert cli.main(["measure"]) == 1
    assert "pw-dump missing" in capsys.readouterr().out


def test_tune_dry_run(monkeypatch, capsys, tmp_path):
    path = tmp_path / "99.conf"
    assert cli.main(["tune", "--profile", "gaming", "--config", str(path), "--dry-run"]) == 0
    assert not path.exists()
    assert "default.clock.quantum = 64" in capsys.readouterr().out


def test_tune_and_restore(monkeypatch, capsys, tmp_path):
    path = tmp_path / "99.conf"
    assert cli.main(["tune", "--profile", "gaming", "--config", str(path)]) == 0
    assert path.exists()
    assert cli.main(["restore", "--config", str(path)]) == 0
    assert not path.exists()


def test_doctor_json(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli, "collect_state", _state)
    path = tmp_path / "99.conf"
    code = cli.main(["doctor", "--config", str(path), "--json"])
    assert code in (0, 1)
    payload = json.loads(capsys.readouterr().out)
    assert "checks" in payload
    assert "failures" in payload
    assert isinstance(payload["checks"], list)
