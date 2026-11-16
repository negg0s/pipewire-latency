import json

from pipewire_latency.state import PipeWireState, parse_pw_dump, parse_pw_metadata


def test_parse_pw_metadata():
    text = """
Found "settings" metadata 31
update: id:0 key:'clock.force-quantum' value:'64' type:'Spa:String:JSON'
update: id:0 key:'clock.force-rate' value:'48000' type:'Spa:String:JSON'
update: id:0 key:'clock.force-quantum' value:'' type:'Spa:String:JSON'
"""
    values = parse_pw_metadata(text)
    assert values["clock.force-quantum"] == "64"
    assert values["clock.force-rate"] == "48000"


def test_parse_pw_dump():
    payload = [
        {
            "id": 35,
            "type": "PipeWire:Interface:Node",
            "info": {
                "props": {
                    "node.name": "alsa_output.pci-0000_00_1f.3.analog-stereo",
                    "media.class": "Audio/Sink",
                    "node.driver": True,
                    "clock.quantum": 256,
                    "clock.rate": 48000,
                }
            },
        },
        {
            "id": 40,
            "type": "PipeWire:Interface:Node",
            "info": {
                "props": {
                    "node.name": "application.name",
                    "media.class": "Stream/Output/Audio",
                }
            },
        },
    ]
    quantum, rate, driver, nodes = parse_pw_dump(json.dumps(payload))
    assert quantum == 256
    assert rate == 48000
    assert driver == "alsa_output.pci-0000_00_1f.3.analog-stereo"
    assert len(nodes) == 2


def test_parse_pw_dump_bad_json():
    assert parse_pw_dump("not json") == (None, None, None, ())


def test_buffer_ms():
    state = PipeWireState(quantum=64, rate=48000)
    assert state.buffer_ms is not None
    assert round(state.buffer_ms, 3) == 1.333
    assert state.is_complete is True


def test_buffer_ms_invalid_values():
    assert PipeWireState(quantum=0, rate=48000).buffer_ms is None
    assert PipeWireState(quantum=-64, rate=48000).buffer_ms is None
    assert PipeWireState(quantum=64, rate=0).buffer_ms is None
    assert PipeWireState(quantum=64, rate=-48000).buffer_ms is None
    assert PipeWireState(quantum=0, rate=0).buffer_ms is None
    assert PipeWireState(quantum=-64, rate=-48000).buffer_ms is None
    assert PipeWireState(quantum=None, rate=48000).buffer_ms is None
    assert PipeWireState(quantum=64, rate=None).buffer_ms is None


def test_report_with_none_buffer(tmp_path):
    from pipewire_latency.report import render_info, render_json, render_report, state_payload

    state = PipeWireState(quantum=0, rate=0)
    assert state.buffer_ms is None

    payload = state_payload(state)
    assert payload["buffer_ms"] is None

    json_str = render_json(state)
    assert '"buffer_ms": null' in json_str

    info_str = render_info(state)
    assert "buffer  : unknown" in info_str

    report_str = render_report(state, None, tmp_path / "99.conf")
    assert "PipeWire latency report" in report_str
