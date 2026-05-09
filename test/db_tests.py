import pytest
import os

from backend import remote_persistence


def test_resolve_db_url_or_skip():
    try:
        url = remote_persistence._resolve_db_url(None)
    except RuntimeError:
        pytest.skip("No remote DB configured; skipping DB integration tests")

    assert isinstance(url, str) and url
