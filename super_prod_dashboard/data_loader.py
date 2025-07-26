import json
import os
import glob
from datetime import datetime
from pathlib import Path
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
        """
        Find all JSON files in the specified directories.
        
        Returns:
            list: List of file paths with their modification times
        """
        json_files = []
        
        for directory in self.backup_directories:
            if not os.path.exists(directory):
                continue
                
            # Search for JSON files in the directory
            pattern = os.path.join(directory, "*.json")
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    # Get file modification time
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
        """
        Find the most recent JSON file based on modification time.
        
        Args:
            json_files: List of file dictionaries with path and mtime
            
        Returns:
            Optional[Dict]: The most recent file info or None if no files found
        """
        if not json_files:
            return None
        
        # Sort by modification time (most recent first)
        sorted_files = sorted(json_files, key=lambda x: x['mtime'], reverse=True)
        return sorted_files[0]
    
    def validate_super_productivity_file(self, file_path: str) -> bool:
        """
        Validate that the JSON file is a valid SuperProductivity backup.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            bool: True if file is valid SuperProductivity backup
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it has the expected SuperProductivity structure
            # Backup files have entities directly at root level
            # Original files have entities nested under 'data' key
            expected_entities = ['task', 'project']
            
            # Check if entities are at root level (backup format)
            if all(entity in data for entity in expected_entities):
                return True
            
            # Check if entities are nested under 'data' key (original format)
            if 'data' in data:
                data_section = data['data']
                if all(entity in data_section for entity in expected_entities):
                    return True
            
            return False
            
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Warning: Invalid SuperProductivity file {file_path}: {e}")
            return False
    
    def load_data(self) -> Dict[str, Any]:
        """
        Load the most recent SuperProductivity backup data.
        
        Returns:
            Dict[str, Any]: The loaded JSON data
            
        Raises:
            FileNotFoundError: If no valid SuperProductivity backup files are found
            ValueError: If the loaded file is not a valid SuperProductivity backup
        """
        # Find all JSON files
        json_files = self.find_json_files()
        
        if not json_files:
            raise FileNotFoundError(
                "No JSON files found in the specified directories. "
                f"Searched in: {', '.join(self.backup_directories)}"
            )
        
        # Get the most recent file
        most_recent = self.get_most_recent_file(json_files)
        
        if not most_recent:
            raise FileNotFoundError("No valid JSON files found")
        
        file_path = most_recent['path']
        print(f"Loading data from: {file_path}")
        print(f"File modified: {most_recent['datetime']}")
        
        # Validate the file
        if not self.validate_super_productivity_file(file_path):
            raise ValueError(f"File {file_path} is not a valid SuperProductivity backup")
        
        # Load the data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalize the data structure
            # If entities are at root level (backup format), wrap them in a 'data' key
            # This ensures consistent structure for the dashboard
            if 'task' in data and 'project' in data and 'data' not in data:
                # This is a backup format file, normalize it
                normalized_data = {'data': data}
                print(f"Normalized backup format data from {file_path}")
                return normalized_data
            else:
                # This is already in the expected format
                print(f"Successfully loaded SuperProductivity data from {file_path}")
                return data
            
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Error loading JSON file {file_path}: {e}")


def load_super_productivity_data() -> Dict[str, Any]:
    """
    Convenience function to load SuperProductivity data.
    
    Returns:
        Dict[str, Any]: The loaded JSON data
    """
    loader = SuperProductivityDataLoader()
    return loader.load_data()


if __name__ == "__main__":
    # Test the loader
    try:
        data = load_super_productivity_data()
        print("Data loaded successfully!")
        print(f"Available sections: {list(data['data'].keys())}")
    except Exception as e:
        print(f"Error loading data: {e}") 