from test_hotkeys import FakePortalConnection

from cortex_whisper.portals import BACKGROUND_INTERFACE, BackgroundPortal, unwrap_dbus


def test_background_portal_requests_autostart():
    connection = FakePortalConnection()
    results = []
    portal = BackgroundPortal(connection)

    portal.request(True, lambda success, error: results.append((success, error)))

    call = connection.calls[0]
    assert call[0:2] == (BACKGROUND_INTERFACE, "RequestBackground")
    options = unwrap_dbus(call[2][1])
    assert options["autostart"] is True
    assert options["commandline"] == ["cortex-whisper"]
    connection.responses[0][1](0, {"autostart": True})
    assert results == [(True, "")]


def test_background_portal_reports_denial():
    connection = FakePortalConnection()
    results = []
    portal = BackgroundPortal(connection)
    portal.request(True, lambda success, error: results.append((success, error)))

    connection.responses[0][1](2, {})

    assert results == [(False, "background permission was denied (code 2)")]


def test_background_portal_rejects_overlapping_requests():
    connection = FakePortalConnection()
    first = []
    second = []
    portal = BackgroundPortal(connection)
    portal.request(True, lambda success, error: first.append((success, error)))

    portal.request(False, lambda success, error: second.append((success, error)))

    assert first == []
    assert second == [(False, "an automatic-start request is already pending")]
