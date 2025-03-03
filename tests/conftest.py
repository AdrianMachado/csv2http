"""
Global test fixtures
"""

import pathlib
import random

import httpx
import pytest
import respx

from csv2http import core, parser, utils

from .constants import TEST_CSVS

# pylint: disable=fixme


@pytest.fixture(scope="module", params=TEST_CSVS)
def csv_payload_generator_param_fxt(request):
    """Parametrized fixture of csv_payload_generators, one per CSV in tests/data."""
    yield parser.csv_payload_generator(request.param)


@pytest.fixture(scope="module")
def sample_csv() -> pathlib.Path:
    return pathlib.Path(TEST_CSVS[1])


def _reflect_request(request: httpx.Request) -> respx.MockResponse:
    reflect_headers = {"content-type", "content-length"}
    headers = {k: v for (k, v) in request.headers.items() if k in reflect_headers}
    return respx.MockResponse(200, content=request.content, headers=headers)


def _reflect_request_random_status(request: httpx.Request) -> respx.MockResponse:
    response = _reflect_request(request)
    response.status_code = random.choice((200, 200, 201, 202, 401, 403, 404, 422, 500))
    return response


@pytest.fixture
def http_reflect():
    """Return all outgoing http POST | PUT | PATCH request's payload as a response."""
    # TODO: make http_reflect_airgap
    # pylint: disable=not-context-manager
    with respx.mock(assert_all_called=False, assert_all_mocked=True) as respx_mock:

        respx_mock.route(method__in=["POST", "PUT", "PATCH"]).mock(
            side_effect=_reflect_request
        )

        yield respx_mock


@pytest.fixture
def http_reflect_random_status():
    """Randomize status codes. Return all outgoing http request's payload as a response."""
    # pylint: disable=not-context-manager
    with respx.mock(assert_all_called=False, assert_all_mocked=True) as respx_mock:

        respx_mock.route(method__in=["POST", "PUT", "PATCH"]).mock(
            side_effect=_reflect_request_random_status
        )

        yield respx_mock


@pytest.fixture
def tmp_log_files(tmpdir, monkeypatch):
    """
    Creates a temporary directory and patches `core._add_timestamp_and_suffix()`
    to always return a path within that directory.
    """
    tmpdir_path = pathlib.Path(tmpdir)

    def _add_ts_and_suffix_tmpdir(filepath, suffix="log") -> pathlib.Path:
        # pylint: disable=protected-access
        return tmpdir_path / utils._add_timestamp_and_suffix(filepath, suffix)

    monkeypatch.setattr(
        core,
        "_add_timestamp_and_suffix",
        _add_ts_and_suffix_tmpdir,
        raising=True,
    )

    yield tmpdir_path
