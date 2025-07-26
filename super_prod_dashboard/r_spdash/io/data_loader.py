import json
import os
import glob
from datetime import datetime
from typing import Dict, Any, Optional

class SuperProductivityDataLoader:
    """
    A class to handle loading SuperProductivity backup JSON files.
    Searches for the most recent backup file from multiple locations.
    """
    def __init__(self):
        self.backup_directories = [
            r"C:\Users\redaa\AppData\Roaming\superProductivity\backups",
            "."  # Current project directory
        ]

    def find_json_files(self) -> list:
        json_files = []
        for directory in self.backup_directories:
            if not os.path.exists(directory):
                continue
            pattern = os.path.join(directory, "*.json")
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    mtime = os.path.getmtime(file_path)
                    json_files.append({
                        'path': file_path,
                        'mtime': mtime,
                        'datetime': datetime.fromtimestamp(mtime)
                    })
                except (OSError, IOError) as e:
                    print(f"Warning: Could not access file {file_path}: {e}")
        return json_files

    def get_most_recent_file(self, json_files: list) -> Optional[Dict[str, Any]]:
        if not json_files:
            return None
        sorted_files = sorted(json_files, key=lambda x: x['mtime'], reverse=True)
        return sorted_files[0]

    def validate_super_productivity_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            expected_entities = ['task', 'project']
            if all(entity in data for entity in expected_entities):
                return True
            if 'data' in data:
                data_section = data['data']
                if all(entity in data_section for entity in expected_entities):
                    return True
            return False
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Warning: Invalid SuperProductivity file {file_path}: {e}")
            return False

    def load_data(self) -> Dict[str, Any]:
        json_files = self.find_json_files()
        if not json_files:
            raise FileNotFoundError(
                "No JSON files found in the specified directories. "
                f"Searched in: {', '.join(self.backup_directories)}"
            )
        most_recent = self.get_most_recent_file(json_files)
        if not most_recent:
            raise FileNotFoundError("No valid JSON files found")
        file_path = most_recent['path']
        print(f"Loading data from: {file_path}")
        print(f"File modified: {most_recent['datetime']}")
        if not self.validate_super_productivity_file(file_path):
            raise ValueError(f"File {file_path} is not a valid SuperProductivity backup")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'task' in data and 'project' in data and 'data' not in data:
                normalized_data = {'data': data}
                print(f"Normalized backup format data from {file_path}")
                return normalized_data
            else:
                print(f"Successfully loaded SuperProductivity data from {file_path}")
                return data
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Error loading JSON file {file_path}: {e}")

def load_super_productivity_data() -> Dict[str, Any]:
    loader = SuperProductivityDataLoader()
    return loader.load_data() 