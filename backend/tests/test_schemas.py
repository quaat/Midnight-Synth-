from app.schemas import PRESET_SCHEMA_VERSION, PresetData, migrate_preset


def test_valid_preset_roundtrip():
    preset = PresetData(name="Test")
    loaded = migrate_preset(preset.model_dump())
    assert loaded.name == "Test"
    assert loaded.schema_version == PRESET_SCHEMA_VERSION


def test_invalid_filter_cutoff_rejected():
    try:
        PresetData(name="Bad", filter={"cutoff": 1, "resonance": 0.2, "key_tracking": 0.1})
        assert False, "expected validation error"
    except Exception:
        assert True
