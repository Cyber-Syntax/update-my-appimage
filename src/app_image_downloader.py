import os
import json
import sys
import logging
import requests
from tqdm import tqdm
from dataclasses import dataclass, field
from src.decorators import handle_api_errors, handle_common_errors
from src.version_manager import VersionManager


@dataclass
class AppImageDownloader:
    """This class downloads the appimage from the github release page"""

    owner: str = None
    repo: str = None
    api_url: str = None
    sha_name: str = None
    sha_url: str = None
    appimage_name: str = None
    version: str = None
    appimage_folder: str = field(default_factory=lambda: "~/Documents/appimages")
    appimage_folder_backup: str = field(
        default_factory=lambda: "~/Documents/appimages/backup"
    )
    hash_type: str = None
    url: str = None
    choice: int = None
    appimages: dict = field(default_factory=dict)
    file_path: str = "config_files/"
    version_manager: VersionManager = field(default_factory=VersionManager)

    def create_versions_json(self):
        """Create versions.json file from config_files."""
        config_files = [
            file for file in os.listdir(self.file_path) if file.endswith(".json")
        ]

        for config_file in config_files:
            config_path = os.path.join(self.file_path, config_file)
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = json.load(file)
                owner = config_data["owner"]
                repo = config_data["repo"]

                # Fetch version info from GitHub API
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                response = requests.get(api_url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    version = data["tag_name"].replace("v", "")
                    appimage_name = next(
                        (
                            asset["name"]
                            for asset in data["assets"]
                            if asset["name"].endswith(".AppImage")
                        ),
                        None,
                    )

                    if version and appimage_name:
                        self.version_manager.add_version(
                            owner, repo, version, appimage_name
                        )
                    else:
                        print(f"Failed to fetch version info for {repo}")
                else:
                    print(
                        f"Failed to fetch version info for {repo} from API: {api_url}"
                    )

        # Save the versions to versions.json
        self.version_manager.save_versions()
        print("versions.json file created.")

    # TODO: is try except needed or decorator handle it?
    @handle_common_errors
    def ask_user(self):
        """New appimage installation options"""
        while True:
            print("Choose one of the following options:")
            print("====================================")
            print("1. Download new appimage, save old appimage")
            print("2. Download new appimage, don't save old appimage")
            print("====================================")
            try:
                self.choice = int(input("Enter your choice: "))

                if self.choice not in [1, 2]:
                    print("Invalid choice. Try again.")
                    self.ask_user()
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    # TODO: Is while true realy needed ?
    @handle_common_errors
    def learn_owner_repo(self):
        while True:
            # Parse the owner and repo from the URL
            print("Parsing the owner and repo from the url...")
            self.owner = self.url.split("/")[3]
            self.repo = self.url.split("/")[4]
            self.url = f"https://github.com/{self.owner}/{self.repo}"
            break

    def list_json_files(self):
        """List the json files in the current directory, if json file exists."""
        try:
            json_files = [
                file for file in os.listdir(self.file_path) if file.endswith(".json")
            ]
        except FileNotFoundError as error:
            logging.error(f"Error: {error}", exc_info=True)
            print(f"\033[41;30mError: {error}. Exiting...\033[0m")
            self.ask_inputs()

        if len(json_files) > 1:
            print("\nAvailable json files:")
            print("================================================================")
            for index, file in enumerate(json_files):
                print(f"{index + 1}. {file}")
            try:
                print(
                    "================================================================"
                )
                choice = int(input("Enter your choice: "))
            except ValueError as error2:
                logging.error(f"Error: {error2}", exc_info=True)
                print("Invalid choice. Please write a number.")
                self.list_json_files()
            else:
                self.repo = json_files[choice - 1].replace(".json", "")
                self.load_credentials()
        elif len(json_files) == 1:
            self.repo = json_files[0].replace(".json", "")
            self.load_credentials()
        else:
            print("There is no .json file in the current directory")
            self.ask_inputs()

    @handle_common_errors
    def ask_inputs(self):
        while True:
            print("=================================================")
            self.url = input("Enter the app github url: ").strip(" ")
            self.appimage_folder = (
                input(
                    "Which directory to save appimage \n"
                    "(Default: '~/Documents/appimages/' if you leave it blank):"
                ).strip(" ")
                or self.appimage_folder
            )
            self.appimage_folder_backup = (
                input(
                    "Which directory to save old appimage \n"
                    "(Default: '~/Documents/appimages/backup/' if you leave it blank):"
                ).strip(" ")
                or self.appimage_folder_backup
            )

            self.hash_type = input(
                "Enter the hash type for your sha(sha256, sha512) file: "
            ).strip(" ")
            print("=================================================")

            if (
                self.url
                and self.appimage_folder
                and self.hash_type
                and self.appimage_folder_backup
            ):
                break

    @handle_common_errors
    def load_credentials(self):
        """Load the credentials from a json file"""
        json_path = f"{self.file_path}{self.repo}.json"
        if os.path.exists(json_path):
            with open(
                f"{self.file_path}{self.repo}.json", "r", encoding="utf-8"
            ) as file:
                self.appimages = json.load(file)
            self.owner = self.appimages["owner"]
            self.repo = self.appimages["repo"]
            self.appimage_name = self.appimages["appimage"]
            self.version = self.appimages["version"]
            self.sha_name = self.appimages["sha"]
            self.choice = self.appimages["choice"]
            self.hash_type = self.appimages["hash_type"]

            if self.appimages["appimage_folder"].startswith("~"):
                self.appimage_folder = os.path.expanduser(
                    self.appimages["appimage_folder"]
                )
            else:
                self.appimage_folder = self.appimages["appimage_folder"]

            if self.appimages["appimage_folder_backup"].startswith("~"):
                self.appimage_folder_backup = os.path.expanduser(
                    self.appimages["appimage_folder_backup"]
                )
            else:
                self.appimage_folder_backup = self.appimages["appimage_folder_backup"]

        else:
            print(
                f"{self.file_path}{self.repo}.json"
                "File not found while trying to load credentials or unknown error."
            )
            self.ask_user()

    @handle_api_errors
    def get_response(self):
        """get the api response from the github api"""
        self.api_url = (
            # TODO: specific tag, maybe feature enhancement
            # https://api.github.com/repos/johannesjo/super-productivity/releases/tags/v10.0.11
            f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"
        )

        # get the api response
        response = requests.get(self.api_url, timeout=10)

        if response is None:
            print("-------------------------------------------------")
            print(f"Failed to get response from API: {self.api_url}")
            print("-------------------------------------------------")
            return

        # check the response status code
        if response.status_code == 200:
            # get the download url from the api
            data = json.loads(response.text)
            # get the version from the tag_name, remove the v from the version
            self.version = data["tag_name"].replace("v", "")

            # version control
            if self.choice in [3, 4]:
                if self.version == self.appimages["version"]:
                    print(f"{self.repo}.AppImage is up to date")
                    print(f"Version: {self.version}")
                    print("Exiting...")
                    sys.exit()
                else:
                    print("-------------------------------------------------")
                    print(f"Current version: {self.appimages['version']}")
                    print(f"\033[42mLatest version: {self.version}\033[0m")
                    print("-------------------------------------------------")

            # Define keywords for the assets
            keywords = {
                "linux",
                "sum",
                "sha",
                "SHA",
                "SHA256",
                "SHA512",
                "SHA-256",
                "SHA-512",
                "checksum",
                "checksums",
                "CHECKSUM",
                "CHECKSUMS",
            }
            valid_extensions = {
                ".sha256",
                ".sha512",
                ".yml",
                ".yaml",
                ".txt",
                ".sum",
                ".sha",
            }

            # get the download url from the assets
            for asset in data["assets"]:
                if asset["name"].endswith(".AppImage"):
                    self.appimage_name = asset["name"]
                    self.url = asset["browser_download_url"]
                elif any(keyword in asset["name"] for keyword in keywords) and asset[
                    "name"
                ].endswith(tuple(valid_extensions)):
                    self.sha_name = asset["name"]
                    self.sha_url = asset["browser_download_url"]
                    if self.sha_name is None:
                        print("Couldn't find the sha file")
                        logging.error("Couldn't find the sha file")
                        # ask user exact SHA name
                        self.sha_name = input("Enter the exact sha name: ")
                        self.sha_url = asset["browser_download_url"]

    @handle_api_errors
    def download(self):
        """Download the appimage from the github api"""
        # Check if the appimage already exists
        if os.path.exists(self.appimage_name) or os.path.exists(
            self.repo + ".AppImage"
        ):
            print(f"{self.appimage_name} already exists in the current directory")
            return

        print(
            f"{self.repo} downloading..."
            "Grab a cup of coffee :), "
            "it will take some time depending on your internet speed."
        )
        # Request the appimage from the url
        response = requests.get(self.url, timeout=10, stream=True)

        total_size_in_bytes = int(response.headers.get("content-length", 0))

        if response.status_code == 200:
            # save the appimage to the appimage folder
            with open(f"{self.appimage_name}", "wb") as file, tqdm(
                desc=self.appimage_name,
                total=total_size_in_bytes,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as progress_bar:
                for data in response.iter_content(chunk_size=8192):
                    size = file.write(data)
                    progress_bar.update(size)
        else:
            print(f"\033[41;30mError downloading {self.appimage_name}\033[0m")
            logging.error(f"Error downloading {self.appimage_name}")
            sys.exit()

        # save the credentials to a json file
        with open(f"{self.file_path}{self.repo}.json", "w", encoding="utf-8") as file:
            json.dump(self.appimages, file, indent=4)

        # make sure to close the response
        if response is not None:
            response.close()
            print("-------------------------------------------------")
            print(f"\033[42mDownload completed! {self.appimage_name} installed.\033[0m")
            print("-------------------------------------------------")
        else:
            print("-------------------------------------------------")
            print(f"\033[41;30mError downloading {self.appimage_name}\033[0m")
            print("-------------------------------------------------")

    @handle_common_errors
    def update_json(self):
        """Update the json file with the new credentials (e.g change json file)"""
        with open(f"{self.file_path}{self.repo}.json", "r", encoding="utf-8") as file:
            self.appimages = json.load(file)

        print("=================================================")
        print("1. sha_name")
        print("2. hash_type")
        print("3. choice")
        print("4. appimage_folder")
        print("5. appimage_folder_backup")
        print("6. Exit")
        print("=================================================")

        choice = int(input("Enter your choice: "))
        if choice == 1:
            self.appimages["sha_name"] = input("Enter the sha name: ")
        elif choice == 2:
            self.appimages["hash_type"] = input("Enter the hash type: ")
        elif choice == 3:
            self.appimages["choice"] = int(input("Enter the choice: "))
        elif choice == 4:
            new_folder = input("Enter new appimage folder: ")
            if not new_folder.endswith("/"):
                new_folder += "/"

            self.appimages["appimage_folder"] = new_folder
        elif choice == 5:
            new_folder = input("Enter new appimage folder backup: ")
            if not new_folder.endswith("/"):
                new_folder += "/"

            self.appimages["appimage_folder_backup"] = new_folder
        elif choice == 6:
            sys.exit()
        else:
            print("Invalid choice")
            sys.exit()
        # save the credentials to a json file
        with open(f"{self.file_path}{self.repo}.json", "w", encoding="utf-8") as file:
            json.dump(self.appimages, file, indent=4)

        print("-------------------------------------------------")
        print("\033[42mCredentials updated successfully\033[0m")
        print("-------------------------------------------------")
