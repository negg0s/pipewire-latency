import pytest

from pipewire_latency.profiles import PROFILES, get_profile, quantum_ms


def test_quantum_ms():
    assert quantum_ms(64, 48000) == pytest.approx(1.3333, rel=1e-3)
    assert quantum_ms(1024, 48000) == pytest.approx(21.3333, rel=1e-3)


def test_quantum_ms_rejects_bad_values():
    with pytest.raises(ValueError):
        quantum_ms(0, 48000)
    with pytest.raises(ValueError):
        quantum_ms(64, 0)


def test_profiles_are_ordered_by_latency():
    assert PROFILES["pro-audio"].buffer_ms < PROFILES["gaming"].buffer_ms
    assert PROFILES["gaming"].buffer_ms < PROFILES["music"].buffer_ms
    assert PROFILES["music"].buffer_ms < PROFILES["balanced"].buffer_ms
    assert PROFILES["balanced"].buffer_ms < PROFILES["safe"].buffer_ms


def test_get_profile_error_lists_names():
    with pytest.raises(ValueError, match="gaming"):
        get_profile("missing")
