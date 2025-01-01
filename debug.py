import json
import os
import requests
from unittest.mock import patch, mock_open, MagicMock
from src.file_handler import FileHandler


# Mock the listdir to return a list of JSON files
def mock_listdir(path):
    return ["mockRepo.json", "mockRepo2.json"]


# Mock the open function to read the mock configuration files
def mock_open_function(file, *args, **kwargs):
    if file.endswith("mockRepo.json"):
        mock_data = {
            "owner": "mockOwner",
            "repo": "mockRepo",
            "appimage": "mockRepo-1.0.0.AppImage",
            "version": "1.0.0",
            "sha": "mock-latest-linux.yml",
            "hash_type": "sha512",
            "choice": 2,
            "appimage_folder_backup": "~/Documents/mockAppimages/backup/",
            "appimage_folder": "~/Documents/mockAppimages/",
        }
    elif file.endswith("mockRepo2.json"):
        mock_data = {
            "owner": "mockOwner2",
            "repo": "mockRepo2",
            "appimage": "mockRepo2-1.0.0.AppImage",
            "version": "1.0.0",
            "sha": "mock-latest-linux.yml",
            "hash_type": "sha512",
            "choice": 2,
            "appimage_folder_backup": "~/Documents/mockAppimages/backup/",
            "appimage_folder": "~/Documents/mockAppimages/",
        }
    else:
        return open(file, *args, **kwargs)

    return mock_open(read_data=json.dumps(mock_data))()


# Mock the requests.get function to simulate GitHub API response
def mock_requests_get(url, *args, **kwargs):
    if url is None:
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        return mock_response

    mock_response = MagicMock()
    if "mockRepo" in url:
        mock_response.json.return_value = {"tag_name": "v1.1.0"}
    elif "mockRepo2" in url:
        mock_response.json.return_value = {"tag_name": "v2.1.0"}
    return mock_response


# Main function to test check_updates_json_all
def main():
    with patch("os.listdir", side_effect=mock_listdir):
        with patch("builtins.open", new_callable=lambda: mock_open_function):
            with patch("requests.get", side_effect=mock_requests_get):
                # Initialize FileHandler object
                file_handler = FileHandler()
                file_handler.file_path = "config_files/"

                # Run check_updates_json_all and capture output
                file_handler.check_updates_json_all()


if __name__ == "__main__":
    main()
