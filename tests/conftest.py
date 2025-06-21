"""
Pytest configuration and fixtures for File Organizer Tool tests.
"""
import os
import tempfile
import shutil
import pytest
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_files_dir(temp_dir):
    """Create a temporary directory with sample files for testing."""
    temp_path = Path(temp_dir)
    
    # Create various test files
    test_files = [
        "project-main.py",
        "project-utils.py", 
        "project-config.json",
        "docs-readme.md",
        "docs-api.md",
        "test-unit.py",
        "test-integration.py",
        "image-photo1.jpg",
        "image-photo2.png",
        "video-movie.mp4",
        "audio-song.mp3",
        "no_separator_file.txt",
        "another_file_without_dash.pdf"
    ]
    
    for file_name in test_files:
        file_path = temp_path / file_name
        file_path.write_text(f"Content of {file_name}")
    
    return str(temp_path)


@pytest.fixture
def organized_dir(temp_dir):
    """Create a directory with already organized structure for testing reversal."""
    temp_path = Path(temp_dir)
    
    # Create subdirectories and files
    subdirs = {
        "project": ["main.py", "utils.py", "config.json"],
        "docs": ["readme.md", "api.md"],
        "test": ["unit.py", "integration.py"],
        "image": ["photo1.jpg", "photo2.png"]
    }
    
    for subdir, files in subdirs.items():
        subdir_path = temp_path / subdir
        subdir_path.mkdir()
        for file_name in files:
            file_path = subdir_path / file_name
            file_path.write_text(f"Content of {file_name}")
    
    return str(temp_path)


@pytest.fixture
def complex_nested_dir(temp_dir):
    """Create a complex nested directory structure for tree testing."""
    temp_path = Path(temp_dir)
    
    # Create complex structure
    structure = {
        "src": {
            "main": ["app.py", "config.py"],
            "utils": ["helpers.py", "validators.py"],
            "tests": ["test_main.py"]
        },
        "docs": {
            "api": ["endpoints.md"],
            "guides": ["setup.md", "usage.md"]
        },
        "data": ["sample.json", "config.yaml"],
        ".hidden": [".env", ".gitignore"]
    }
    
    def create_structure(base_path, struct):
        for item, content in struct.items():
            if isinstance(content, dict):
                # It's a directory
                dir_path = base_path / item
                dir_path.mkdir()
                create_structure(dir_path, content)
            else:
                # It's a list of files
                dir_path = base_path / item
                dir_path.mkdir()
                for file_name in content:
                    file_path = dir_path / file_name
                    file_path.write_text(f"Content of {file_name}")
    
    create_structure(temp_path, structure)
    return str(temp_path)


@pytest.fixture
def empty_dir(temp_dir):
    """Create an empty directory for testing."""
    return temp_dir


@pytest.fixture
def non_existent_dir():
    """Return a path to a non-existent directory."""
    return "/path/that/does/not/exist"


@pytest.fixture
def mock_locale_manager():
    """Create a mock locale manager for testing."""
    class MockLocaleManager:
        def __init__(self):
            self.current_lang = "en"
            self.translations = {
                "error_title": "Error",
                "success_title": "Success",
                "export_tree_save_title": "Save Directory Tree",
                "txt_files": "Text files",
                "all_files": "All files",
                "status_generating_tree": "Generating tree...",
                "status_tree_exported": "Tree exported",
                "export_tree_success": "Tree saved to: {file}",
                "error_exporting_tree": "Error exporting tree: {error}"
            }
        
        def get_string(self, key, **kwargs):
            return self.translations.get(key, key).format(**kwargs)
        
        def get_current_language_code(self):
            return self.current_lang
    
    return MockLocaleManager()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Store original working directory
    original_cwd = os.getcwd()
    
    yield
    
    # Restore original working directory
    os.chdir(original_cwd) 