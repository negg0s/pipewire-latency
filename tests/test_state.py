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
