"""
Tests for CLI functionality in main.py.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, call
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import handle_cli_mode, main


class MockArgs:
    """Mock argparse.Namespace for testing."""
    def __init__(self, **kwargs):
        self.directory = kwargs.get('directory', None)
        self.separator = kwargs.get('separator', '-')
        self.remove_prefix = kwargs.get('remove_prefix', False)
        self.verbose = kwargs.get('verbose', False)
        self.yes = kwargs.get('yes', False)
        self.reverse = kwargs.get('reverse', False)
        self.export_tree = kwargs.get('export_tree', False)
        self.output = kwargs.get('output', None)
        self.show_hidden = kwargs.get('show_hidden', False)
        self.max_depth = kwargs.get('max_depth', None)


class TestHandleCLIMode:
    """Test the handle_cli_mode function."""
    
    @pytest.mark.unit
    def test_cli_nonexistent_directory(self):
        """Test CLI with non-existent directory."""
        args = MockArgs(directory="/nonexistent/path")
        result = handle_cli_mode(args)
        assert result == 1  # Should return error code
    
    @pytest.mark.unit
    def test_cli_export_tree_basic(self, sample_files_dir):
        """Test CLI export tree functionality."""
        output_file = os.path.join(sample_files_dir, "test_tree.txt")
        args = MockArgs(
            directory=sample_files_dir,
            export_tree=True,
            output=output_file
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        assert os.path.exists(output_file)
        
        # Check content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0
    
    @pytest.mark.unit
    def test_cli_export_tree_default_output(self, sample_files_dir):
        """Test CLI export tree with default output filename."""
        args = MockArgs(
            directory=sample_files_dir,
            export_tree=True
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        
        # Check default output file was created
        expected_output = f"{os.path.basename(sample_files_dir)}_tree.txt"
        assert os.path.exists(expected_output)
        
        # Cleanup
        if os.path.exists(expected_output):
            os.remove(expected_output)
    
    @pytest.mark.unit
    def test_cli_export_tree_with_options(self, complex_nested_dir):
        """Test CLI export tree with additional options."""
        output_file = os.path.join(complex_nested_dir, "tree_with_options.txt")
        args = MockArgs(
            directory=complex_nested_dir,
            export_tree=True,
            output=output_file,
            show_hidden=True,
            max_depth=2
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        assert os.path.exists(output_file)
    
    @pytest.mark.unit
    def test_cli_organization_basic(self, sample_files_dir):
        """Test CLI organization functionality."""
        args = MockArgs(
            directory=sample_files_dir,
            yes=True,  # Skip confirmation
            verbose=True
        )
        
        with patch('builtins.print') as mock_print:
            result = handle_cli_mode(args)
            assert result == 0
            
            # Check that verbose output was printed
            assert mock_print.called
    
    @pytest.mark.unit
    def test_cli_organization_with_prefix_removal(self, sample_files_dir):
        """Test CLI organization with prefix removal."""
        args = MockArgs(
            directory=sample_files_dir,
            remove_prefix=True,
            yes=True
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        
        # Check that files were organized
        assert os.path.exists(os.path.join(sample_files_dir, 'project'))
        assert os.path.exists(os.path.join(sample_files_dir, 'docs'))
    
    @pytest.mark.unit
    @patch('builtins.input', return_value='n')
    def test_cli_organization_cancelled(self, mock_input, sample_files_dir):
        """Test CLI organization cancelled by user."""
        args = MockArgs(
            directory=sample_files_dir,
            yes=False  # Require confirmation
        )
        
        result = handle_cli_mode(args)
        assert result == 0  # Should exit cleanly
    
    @pytest.mark.unit
    def test_cli_reverse_basic(self, organized_dir):
        """Test CLI reverse functionality."""
        args = MockArgs(
            directory=organized_dir,
            reverse=True,
            yes=True
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        
        # Check that files were moved back
        files = [f for f in os.listdir(organized_dir) if os.path.isfile(os.path.join(organized_dir, f))]
        assert len(files) > 0
    
    @pytest.mark.unit
    def test_cli_reverse_no_subdirs(self, empty_dir):
        """Test CLI reverse with no subdirectories."""
        args = MockArgs(
            directory=empty_dir,
            reverse=True,
            yes=True
        )
        
        result = handle_cli_mode(args)
        assert result == 1  # Should return error code
    
    @pytest.mark.unit
    @patch('builtins.input', return_value='n')
    def test_cli_reverse_cancelled(self, mock_input, organized_dir):
        """Test CLI reverse cancelled by user."""
        args = MockArgs(
            directory=organized_dir,
            reverse=True,
            yes=False
        )
        
        result = handle_cli_mode(args)
        assert result == 0  # Should exit cleanly
    
    @pytest.mark.unit
    def test_cli_custom_separator(self, temp_dir):
        """Test CLI with custom separator."""
        # Create files with underscore separator
        test_files = ["project_main.py", "docs_readme.md", "test_unit.py"]
        for filename in test_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write('test content')
        
        args = MockArgs(
            directory=temp_dir,
            separator='_',
            yes=True
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        
        # Check that directories were created with correct names
        assert os.path.exists(os.path.join(temp_dir, 'project'))
        assert os.path.exists(os.path.join(temp_dir, 'docs'))


class TestMainFunction:
    """Test the main function."""
    
    @pytest.mark.unit
    @patch('sys.argv', ['main.py'])
    @patch('tkinter.Tk')
    @patch('gui_organizer.FileOrganizerApp')
    def test_main_gui_mode(self, mock_app, mock_tk):
        """Test main function in GUI mode."""
        mock_root = mock_tk.return_value
        
        result = main()
        
        assert result == 0
        mock_tk.assert_called_once()
        mock_app.assert_called_once_with(mock_root)
        mock_root.mainloop.assert_called_once()
    
    @pytest.mark.unit
    @patch('sys.argv', ['main.py', '/test/path', '--export-tree'])
    @patch('main.handle_cli_mode')
    def test_main_cli_mode(self, mock_handle_cli):
        """Test main function in CLI mode."""
        mock_handle_cli.return_value = 0
        
        result = main()
        
        assert result == 0
        mock_handle_cli.assert_called_once()
    
    @pytest.mark.unit
    @patch('sys.argv', ['main.py', '--help'])
    def test_main_help(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # argparse exits with code 0 for help
        assert exc_info.value.code == 0


@pytest.mark.integration  
class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_full_cli_workflow(self, sample_files_dir):
        """Test complete CLI workflow: organize -> export tree -> reverse."""
        # Step 1: Organize files
        organize_args = MockArgs(
            directory=sample_files_dir,
            remove_prefix=True,
            yes=True
        )
        
        result = handle_cli_mode(organize_args)
        assert result == 0
        
        # Step 2: Export tree structure
        tree_output = os.path.join(sample_files_dir, "organized_tree.txt")
        export_args = MockArgs(
            directory=sample_files_dir,
            export_tree=True,
            output=tree_output
        )
        
        result = handle_cli_mode(export_args)
        assert result == 0
        assert os.path.exists(tree_output)
        
        # Step 3: Reverse organization
        reverse_args = MockArgs(
            directory=sample_files_dir,
            reverse=True,
            yes=True
        )
        
        result = handle_cli_mode(reverse_args)
        assert result == 0
        
        # Verify files are back in main directory
        files = [f for f in os.listdir(sample_files_dir) 
                if os.path.isfile(os.path.join(sample_files_dir, f))]
        assert len(files) > 0
        
        # Tree file should still exist
        assert os.path.exists(tree_output)
    
    @pytest.mark.slow
    def test_cli_with_large_directory_structure(self, temp_dir):
        """Test CLI with a large directory structure."""
        # Create a large nested structure
        base_path = Path(temp_dir)
        
        for i in range(10):
            for j in range(5):
                dir_path = base_path / f"category{i}" / f"subdir{j}"
                dir_path.mkdir(parents=True, exist_ok=True)
                
                for k in range(3):
                    file_path = dir_path / f"file{k}.txt"
                    file_path.write_text(f"Content {i}-{j}-{k}")
        
        # Test export tree
        args = MockArgs(
            directory=temp_dir,
            export_tree=True,
            output=os.path.join(temp_dir, "large_tree.txt")
        )
        
        result = handle_cli_mode(args)
        assert result == 0
        
        # Check that the tree file was created and has content
        tree_file = os.path.join(temp_dir, "large_tree.txt")
        assert os.path.exists(tree_file)
        
        with open(tree_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'category0' in content
            assert 'category9' in content
            assert len(content) > 1000  # Should be substantial content


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    @pytest.mark.unit
    def test_cli_permission_error(self):
        """Test CLI with permission errors."""
        # This test might not work on all systems
        if os.name == 'nt':  # Windows
            pytest.skip("Permission test not reliable on Windows")
        
        args = MockArgs(
            directory="/root",  # Likely to cause permission issues
            export_tree=True,
            output="/root/tree.txt"
        )
        
        result = handle_cli_mode(args)
        # Should handle the error gracefully
        assert result in [0, 1]  # Either succeeds or fails gracefully
    
    @pytest.mark.unit
    def test_cli_invalid_max_depth(self, sample_files_dir):
        """Test CLI with invalid max_depth parameter."""
        args = MockArgs(
            directory=sample_files_dir,
            export_tree=True,
            max_depth=-1  # Invalid depth
        )
        
        # Should handle gracefully (negative depth treated as None or 0)
        result = handle_cli_mode(args)
        assert result == 0
    
    @pytest.mark.unit
    @patch('main.generate_directory_tree')
    def test_cli_export_tree_exception(self, mock_generate_tree, sample_files_dir):
        """Test CLI export tree with exception."""
        mock_generate_tree.side_effect = Exception("Test error")
        
        args = MockArgs(
            directory=sample_files_dir,
            export_tree=True
        )
        
        result = handle_cli_mode(args)
        assert result == 1 