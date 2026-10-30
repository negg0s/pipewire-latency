import pytest

from pipewire_latency.config import list_backups, render_config, restore_config, write_config
from pipewire_latency.profiles import get_profile


def test_render_config_contains_profile_values():
    text = render_config(get_profile("gaming"))
    assert "default.clock.quantum = 64" in text
    assert "default.clock.rate = 48000" in text
    assert "default.clock.min-quantum = 16" in text


def test_write_and_restore(tmp_path):
    path = tmp_path / "99-pipewire-latency.conf"
    result = write_config(get_profile("gaming"), path)
    assert result.wrote is True
    assert result.backup is None
    assert path.read_text(encoding="utf-8") == render_config(get_profile("gaming"))

    result = write_config(get_profile("safe"), path, force=True)
    assert result.backup is not None
    assert result.backup.exists()
    assert "default.clock.quantum = 1024" in path.read_text(encoding="utf-8")

    target, backup = restore_config(path)
    assert target == path
    assert backup == result.backup
    assert "default.clock.quantum = 64" in path.read_text(encoding="utf-8")


def test_write_refuses_existing_without_force(tmp_path):
    path = tmp_path / "99-pipewire-latency.conf"
    path.write_text("old", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_config(get_profile("gaming"), path)


def test_dry_run_does_not_write(tmp_path):
    path = tmp_path / "99-pipewire-latency.conf"
    result = write_config(get_profile("gaming"), path, dry_run=True)
    assert result.wrote is False
    assert not path.exists()


def test_restore_without_backup_removes_file(tmp_path):
    path = tmp_path / "99-pipewire-latency.conf"
    path.write_text("generated", encoding="utf-8")
    target, backup = restore_config(path)
    assert target == path
    assert backup is None
    assert not path.exists()


def test_list_backups_sorted(tmp_path):
    path = tmp_path / "99-pipewire-latency.conf"
    first = tmp_path / "99-pipewire-latency.conf.20260101T000000Z.bak"
    second = tmp_path / "99-pipewire-latency.conf.20260102T000000Z.bak"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")
    assert list_backups(path) == [first, second]
