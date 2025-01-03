from dataclasses import dataclass, field
import os
import json


@dataclass
class VersionManager:
    appimage_folder: str = field(default_factory=lambda: "~/Documents/appimages")
    versions: dict = field(default_factory=dict)

    def __post_init__(self):
        self.version_file_path = os.path.join(
            os.path.expanduser(self.appimage_folder), "versions.json"
        )
        self.load_versions()

    def load_versions(self):
        """Load the app versions from the versions.json file."""
        if os.path.exists(self.version_file_path):
            with open(self.version_file_path, "r", encoding="utf-8") as version_file:
                self.versions = json.load(version_file)
        else:
            self.versions = {}

    def save_versions(self):
        """Save the app versions to the versions.json file."""
        with open(self.version_file_path, "w", encoding="utf-8") as version_file:
            json.dump(self.versions, version_file, indent=4)
        print(f"Saved app versions to {self.version_file_path}")

    def add_version(self, repo, version, appimage_name):
        """Add or update an app version."""
        self.versions[repo] = {"version": version, "appimage_name": appimage_name}
        self.save_versions()

    def compare_versions(self, config_versions):
        """Compare versions in versions.json with config_files."""
        discrepancies = []
        for repo, version_info in self.versions.items():
            config_version = config_versions.get(repo)
            if config_version and config_version != version_info["version"]:
                discrepancies.append(
                    f"Discrepancy in {repo}: versions.json={version_info['version']}, config_files={config_version}"
                )

        if discrepancies:
            print("Discrepancies found:")
            for discrepancy in discrepancies:
                print(discrepancy)
        else:
            print("All versions are up to date.")
