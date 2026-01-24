import pytest
import json
import requests
from pytest_mock import MockerFixture
from unittest.mock import Mock

from app.api import fetch_by_reference


class TestFetchByReference:

    @pytest.mark.parametrize("book,chapter,verses,expected_url", [
        ("john", "3", "16", "http://bible-api.com/john+3:16?translation=web"),  # verses with default translation
        ("john", "3", None, "http://bible-api.com/john+3?translation=web")      # chapter with default translation
    ])
    def test_fetch_by_reference_builds_correct_url(
        self,
        mocker: MockerFixture,
        book,
        chapter,
        verses,
        expected_url
    ):
        # Mock response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"reference": "test", "verses": []}


        # Mock requests.get to return our mock response
        mock_get = mocker.patch('app.api.requests.get', return_value=mock_response)

        # Call the function without translation parameter (should default to "web")
        result = fetch_by_reference(book, chapter, verses, use_mock=False)

        # Assertions
        assert result is not None
        mock_get.assert_called_once_with(expected_url, timeout=10)
        mock_response.raise_for_status.assert_called_once()

    
    def test_fetch_by_reference_use_mock(self):
        result = fetch_by_reference("john", "3", "16", use_mock=True)
        assert result is not None
        assert result["reference"] == "John 3:16"


    def test_fetch_by_reference_with_translation_parameter(self, mocker: MockerFixture):
        """Test that translation parameter is correctly added to URL."""
        # Mock response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"reference": "test", "verses": []}
        
        # Mock requests.get to return our mock response
        mock_get = mocker.patch('app.api.requests.get', return_value=mock_response)
        
        # Call the function with explicit translation parameter
        result = fetch_by_reference("john", "3", "16", translation="kjv", use_mock=False)
        
        # Assertions
        assert result is not None
        mock_get.assert_called_once_with("http://bible-api.com/john+3:16?translation=kjv", timeout=10)
        mock_response.raise_for_status.assert_called_once()


    @pytest.mark.parametrize("exception_class", [
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.HTTPError,
])
    def test_fetch_by_reference_handles_errors(self, mocker, exception_class):
        # HTTPError requires special handling because it uses a response object
        if exception_class == requests.exceptions.HTTPError:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            http_error = requests.exceptions.HTTPError()
            http_error.response = mock_response
            mocker.patch('app.api.requests.get', side_effect=http_error)
        else:
            mocker.patch('app.api.requests.get', side_effect=exception_class())
        
        result = fetch_by_reference("John", "3", "16", use_mock=False)
        assert result is None
    

    def test_fetch_by_reference_handles_request_exception(self, mocker):
        mocker.patch('app.api.requests.get', side_effect=requests.exceptions.RequestException())
        
        result = fetch_by_reference("John", "3", "16", use_mock=False)
        assert result is None


    def test_fetch_by_reference_handles_json_decode_error(self, mocker):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        mocker.patch('app.api.requests.get', return_value=mock_response)
        
        result = fetch_by_reference("John", "3", "16", use_mock=False)
        assert result is None


    def test_fetch_by_reference_handles_mock_file_not_found(self, mocker):
        mocker.patch('builtins.open', side_effect=FileNotFoundError())
        
        result = fetch_by_reference("John", "3", "16", use_mock=True)
        assert result is None


    def test_fetch_by_reference_handles_mock_json_decode_error(self, mocker):
        mocker.patch('builtins.open', mocker.mock_open(read_data='invalid json'))
        mocker.patch('app.api.json.load', side_effect=json.JSONDecodeError("Invalid", "", 0))
        
        result = fetch_by_reference("John", "3", "16", use_mock=True)
        assert result is None