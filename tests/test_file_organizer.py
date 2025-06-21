"""
Tests for file_organizer.py core functionality.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from file_organizer import (
    get_organization_plan, 
    execute_organization, 
    reverse_organization_action,
    generate_directory_tree
)


class TestGetOrganizationPlan:
    """Test the get_organization_plan function."""
    
    @pytest.mark.unit
    def test_organization_plan_with_default_separator(self, sample_files_dir):
        """Test organization plan with default separator '-'."""
        categories = get_organization_plan(sample_files_dir, '-')
        
        assert 'project' in categories
        assert 'docs' in categories
        assert 'test' in categories
        assert 'image' in categories
        assert 'video' in categories
        assert 'audio' in categories
        assert 'NO_SEPARATOR' in categories
        
        assert 'project-main.py' in categories['project']
        assert 'docs-readme.md' in categories['docs']
        assert 'no_separator_file.txt' in categories['NO_SEPARATOR']
    
    @pytest.mark.unit
    def test_organization_plan_with_custom_separator(self, sample_files_dir):
        """Test organization plan with custom separator '_'."""
        categories = get_organization_plan(sample_files_dir, '_')
        
        assert 'another' in categories
        assert 'another_file_without_dash.pdf' in categories['another']
    
    @pytest.mark.unit
    def test_organization_plan_empty_directory(self, empty_dir):
        """Test organization plan with empty directory."""
        categories = get_organization_plan(empty_dir, '-')
        assert len(categories) == 0
    
    @pytest.mark.unit
    def test_organization_plan_nonexistent_directory(self, non_existent_dir):
        """Test organization plan with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            get_organization_plan(non_existent_dir, '-')
    
    @pytest.mark.unit
    def test_organization_plan_empty_separator(self, sample_files_dir):
        """Test organization plan with empty separator."""
        categories = get_organization_plan(sample_files_dir, '')
        # All files should go to NO_SEPARATOR category
        assert 'NO_SEPARATOR' in categories
        assert len(categories) == 1


class TestExecuteOrganization:
    """Test the execute_organization function."""
    
    @pytest.mark.unit
    def test_execute_organization_basic(self, sample_files_dir):
        """Test basic file organization execution."""
        categories = get_organization_plan(sample_files_dir, '-')
        moved_count, dir_count, errors = execute_organization(
            sample_files_dir, categories, remove_prefix=False, separator='-'
        )
        
        assert moved_count > 0
        assert dir_count > 0
        assert len(errors) == 0
        
        # Check that directories were created
        assert os.path.exists(os.path.join(sample_files_dir, 'project'))
        assert os.path.exists(os.path.join(sample_files_dir, 'docs'))
        
        # Check that files were moved
        assert os.path.exists(os.path.join(sample_files_dir, 'project', 'project-main.py'))
    
    @pytest.mark.unit
    def test_execute_organization_with_prefix_removal(self, sample_files_dir):
        """Test organization with prefix removal."""
        categories = get_organization_plan(sample_files_dir, '-')
        moved_count, dir_count, errors = execute_organization(
            sample_files_dir, categories, remove_prefix=True, separator='-'
        )
        
        assert moved_count > 0
        assert len(errors) == 0
        
        # Check that prefixes were removed
        assert os.path.exists(os.path.join(sample_files_dir, 'project', 'main.py'))
        assert not os.path.exists(os.path.join(sample_files_dir, 'project', 'project-main.py'))
    
    @pytest.mark.unit
    def test_execute_organization_empty_categories(self, sample_files_dir):
        """Test organization with empty categories."""
        moved_count, dir_count, errors = execute_organization(
            sample_files_dir, {}, remove_prefix=False, separator='-'
        )
        
        assert moved_count == 0
        assert dir_count == 0
        assert len(errors) == 0


class TestReverseOrganization:
    """Test the reverse_organization_action function."""
    
    @pytest.mark.unit
    def test_reverse_organization_basic(self, organized_dir):
        """Test basic reverse organization."""
        # Get the organized categories by scanning the existing structure
        organized_categories = {}
        for item in os.listdir(organized_dir):
            item_path = os.path.join(organized_dir, item)
            if os.path.isdir(item_path):
                files = [f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))]
                if files:
                    organized_categories[item] = files
        
        moved_count, removed_dirs, errors = reverse_organization_action(
            organized_dir, organized_categories, False, '-'
        )
        
        assert moved_count > 0
        assert removed_dirs > 0
        assert len(errors) == 0
        
        # Check that files were moved back
        assert os.path.exists(os.path.join(organized_dir, 'main.py'))
        assert os.path.exists(os.path.join(organized_dir, 'readme.md'))
    
    @pytest.mark.unit
    def test_reverse_organization_with_prefix_restoration(self, organized_dir):
        """Test reverse organization with prefix restoration."""
        organized_categories = {}
        for item in os.listdir(organized_dir):
            item_path = os.path.join(organized_dir, item)
            if os.path.isdir(item_path):
                files = [f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))]
                if files:
                    organized_categories[item] = files
        
        moved_count, removed_dirs, errors = reverse_organization_action(
            organized_dir, organized_categories, True, '-'
        )
        
        assert moved_count > 0
        
        # Check that prefixes were restored
        assert os.path.exists(os.path.join(organized_dir, 'project-main.py'))
        assert os.path.exists(os.path.join(organized_dir, 'docs-readme.md'))
    
    @pytest.mark.unit
    def test_reverse_organization_nonexistent_directory(self, non_existent_dir):
        """Test reverse organization with non-existent directory."""
        moved_count, removed_dirs, errors = reverse_organization_action(
            non_existent_dir, {}, False, '-'
        )
        
        assert moved_count == 0
        assert removed_dirs == 0
        assert len(errors) > 0


class TestGenerateDirectoryTree:
    """Test the generate_directory_tree function."""
    
    @pytest.mark.unit
    def test_generate_tree_return_string(self, complex_nested_dir):
        """Test generating tree as return string."""
        tree_content = generate_directory_tree(complex_nested_dir)
        
        assert tree_content is not None
        assert 'src/' in tree_content
        assert 'docs/' in tree_content
        assert '├──' in tree_content or '└──' in tree_content
    
    @pytest.mark.unit
    def test_generate_tree_save_to_file(self, complex_nested_dir, temp_dir):
        """Test generating tree and saving to file."""
        output_file = os.path.join(temp_dir, 'test_tree.txt')
        result = generate_directory_tree(complex_nested_dir, output_file)
        
        assert result is None  # Should return None when saving to file
        assert os.path.exists(output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'src/' in content
            assert 'docs/' in content
    
    @pytest.mark.unit
    def test_generate_tree_with_hidden_files(self, complex_nested_dir):
        """Test generating tree with hidden files included."""
        tree_content = generate_directory_tree(complex_nested_dir, show_hidden=True)
        
        assert '.hidden/' in tree_content
    
    @pytest.mark.unit
    def test_generate_tree_without_hidden_files(self, complex_nested_dir):
        """Test generating tree without hidden files."""
        tree_content = generate_directory_tree(complex_nested_dir, show_hidden=False)
        
        assert '.hidden/' not in tree_content
    
    @pytest.mark.unit
    def test_generate_tree_with_max_depth(self, complex_nested_dir):
        """Test generating tree with maximum depth limit."""
        tree_content = generate_directory_tree(complex_nested_dir, max_depth=1)
        
        # Should only show first level directories
        assert 'src/' in tree_content
        assert 'docs/' in tree_content
        # Should not show deeper nested files
        assert 'app.py' not in tree_content
    
    @pytest.mark.unit
    def test_generate_tree_nonexistent_directory(self, non_existent_dir):
        """Test generating tree for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            generate_directory_tree(non_existent_dir)
    
    @pytest.mark.unit
    def test_generate_tree_permission_error(self, temp_dir):
        """Test generating tree with permission error on file write."""
        output_file = '/root/no_permission.txt'  # Likely to cause permission error
        
        with pytest.raises(PermissionError):
            generate_directory_tree(temp_dir, output_file)
    
    @pytest.mark.unit
    def test_generate_tree_empty_directory(self, empty_dir):
        """Test generating tree for empty directory."""
        tree_content = generate_directory_tree(empty_dir)
        
        # Should contain at least the root directory name
        dir_name = os.path.basename(empty_dir)
        assert f'{dir_name}/' in tree_content or tree_content.strip().endswith('/')


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    def test_organization_with_special_characters_in_filenames(self, temp_dir):
        """Test organization with special characters in filenames."""
        # Create files with special characters
        special_files = [
            "test-file with spaces.txt",
            "test-file@#$.txt",
            "test-file(1).txt",
            "test-file[brackets].txt"
        ]
        
        for filename in special_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write('test content')
        
        categories = get_organization_plan(temp_dir, '-')
        moved_count, dir_count, errors = execute_organization(
            temp_dir, categories, remove_prefix=False, separator='-'
        )
        
        assert moved_count > 0
        assert len(errors) == 0
    
    @pytest.mark.unit
    def test_organization_with_unicode_filenames(self, temp_dir):
        """Test organization with unicode filenames."""
        unicode_files = [
            "test-файл.txt",  # Cyrillic
            "test-文件.txt",   # Chinese
            "test-ファイル.txt", # Japanese
            "test-dosya.txt"   # Turkish
        ]
        
        for filename in unicode_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('test content')
        
        categories = get_organization_plan(temp_dir, '-')
        moved_count, dir_count, errors = execute_organization(
            temp_dir, categories, remove_prefix=False, separator='-'
        )
        
        assert moved_count > 0


@pytest.mark.slow
@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    def test_full_organization_and_reversal_workflow(self, sample_files_dir):
        """Test complete organization followed by reversal."""
        # Step 1: Plan organization
        categories = get_organization_plan(sample_files_dir, '-')
        original_file_count = sum(len(files) for files in categories.values())
        
        # Step 2: Execute organization
        moved_count, dir_count, errors = execute_organization(
            sample_files_dir, categories, remove_prefix=True, separator='-'
        )
        
        assert moved_count == original_file_count
        assert len(errors) == 0
        
        # Step 3: Prepare for reversal
        organized_categories = {}
        for item in os.listdir(sample_files_dir):
            item_path = os.path.join(sample_files_dir, item)
            if os.path.isdir(item_path):
                files = [f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))]
                if files:
                    organized_categories[item] = files
        
        # Step 4: Execute reversal
        reversed_count, removed_dirs, reverse_errors = reverse_organization_action(
            sample_files_dir, organized_categories, True, '-'  # With prefix restoration
        )
        
        assert reversed_count == moved_count
        assert removed_dirs == dir_count
        assert len(reverse_errors) == 0
        
        # Step 5: Verify all files are back with original names
        final_files = [f for f in os.listdir(sample_files_dir) if os.path.isfile(os.path.join(sample_files_dir, f))]
        assert 'project-main.py' in final_files
        assert 'docs-readme.md' in final_files 