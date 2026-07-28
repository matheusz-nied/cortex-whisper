from pulsar_whisper.state import AppState


def test_public_state_values_are_stable():
    assert AppState.RECORDING.value == "recording"
    assert AppState.TRANSCRIBING.value == "transcribing"
    assert AppState.SUCCESS.value == "success"
