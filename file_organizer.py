"""
Core logic for file organization and reversal.

This module provides functions to:
- Plan file organization based on filename prefixes.
- Execute the organization by moving files into subdirectories.
- Plan and execute the reversal of an organization.
- Generate directory tree structure and save to text file.
"""
import os
import shutil
from collections import defaultdict

def get_organization_plan(directory, separator='-'):
    """
    Analyzes files in a directory and groups them by prefix.

    The prefix is determined by the characters before the first occurrence
    of the specified separator. Files without the separator are grouped
    under "NO_SEPARATOR".

    Args:
        directory (str): The path to the directory to analyze.
        separator (str, optional): The character or string used to split
                                   filenames for categorization. Defaults to '-'.

    Returns:
        defaultdict: A dictionary where keys are category names (prefixes)
                     and values are lists of filenames belonging to that category.
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    categories = defaultdict(list)
    for file in files:
        if separator and separator in file: # Ensure separator is not empty
            prefix = file.split(separator, 1)[0].strip()
        else:
            prefix = "NO_SEPARATOR" # Category for files without the separator
        
        # Sanitize prefix to create a valid directory name
        # Replace or remove characters invalid for directory names
        # This is a basic example; more robust sanitization might be needed
        # depending on target filesystems.
        prefix = "".join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in prefix).strip()
        if not prefix: # If prefix becomes empty after sanitization
            prefix = "UNNAMED_CATEGORY"

        categories[prefix].append(file)
    
    return categories

def execute_organization(directory, categories, remove_prefix=False, separator='-'):
    """
    Moves files into subdirectories based on the provided categories.

    Optionally removes prefixes from filenames during the move.

    Args:
        directory (str): The root directory where files are located and
                         subdirectories will be created.
        categories (dict): A dictionary of categories and filenames,
                           as returned by `get_organization_plan`.
        remove_prefix (bool, optional): If True, removes the prefix and separator
                                        from filenames. Defaults to False.
        separator (str, optional): The separator used to identify the prefix.
                                   Defaults to '-'.

    Returns:
        tuple: A tuple containing:
               - moved_count (int): Number of files successfully moved.
               - len(categories) (int): Number of target directories.
               - errors (list): A list of error messages encountered.
    """
    moved_count = 0
    errors = []
    
    for category, files_in_cat in categories.items(): # Renamed 'files' to 'files_in_cat'
        category_dir = os.path.join(directory, category)
        if not os.path.exists(category_dir):
            try:
                os.makedirs(category_dir)
            except OSError as e:
                errors.append(f"Could not create directory '{category_dir}': {e}")
                continue # Skip this category if directory creation fails
        
        for file_item in files_in_cat: # Renamed 'file' to 'file_item'
            src = os.path.join(directory, file_item)
            
            new_name = file_item
            if remove_prefix and separator and separator in file_item:
                parts = file_item.split(separator, 1)
                if len(parts) > 1 and parts[1].strip():
                    new_name = parts[1].strip()
                elif len(parts) > 1 and not parts[1].strip(): # Prefix exists, but rest is empty
                    errors.append(f"'{file_item}' - Filename becomes empty after prefix removal. Keeping original name in category.")
                    # Keep original name but still move to category
                # If separator is not in file_item, new_name remains file_item
            
            dst = os.path.join(category_dir, new_name)
            
            # Check for name conflicts
            if os.path.exists(dst):
                errors.append(f"'{file_item}' -> '{new_name}' - Hedef dosya zaten var")
                continue
                
            try:
                shutil.move(src, dst)
                moved_count += 1
            except Exception as e:
                errors.append(f"'{file_item}' taşınırken hata: {str(e)}")
    
    return moved_count, len(categories), errors


def reverse_organization_action(directory, organized_categories, remove_prefix_on_organize, separator_on_organize):
    """
    Reverses a previous file organization.

    Moves files from subdirectories (categories) back to the main directory.
    If prefixes were removed during organization, it attempts to restore them.
    Empty subdirectories are removed after files are moved.

    Args:
        directory (str): The main directory where subdirectories were created.
        organized_categories (dict): A dictionary where keys are subdirectory names (original categories)
                                     and values are lists of files currently in those subdirectories.
                                     This can be generated by scanning the subdirectories.
        remove_prefix_on_organize (bool): Indicates if prefixes were removed during the
                                          original organization.
        separator_on_organize (str): The separator used during the original organization.

    Returns:
        tuple: A tuple containing:
               - moved_count (int): Number of files successfully moved back.
               - removed_dirs_count (int): Number of empty subdirectories removed.
               - errors (list): A list of error messages.
    """
    moved_count = 0
    removed_dirs_count = 0
    errors = []

    if not os.path.isdir(directory):
        errors.append(f"Main directory not found: {directory}")
        return moved_count, removed_dirs_count, errors

    for category_name, files_in_subdir in organized_categories.items():
        subdir_path = os.path.join(directory, category_name)
        if not os.path.isdir(subdir_path):
            # This might happen if a category was planned but never created or manually deleted
            # errors.append(f"Subdirectory '{subdir_path}' not found for reversal.")
            continue

        for filename in files_in_subdir:
            src_path = os.path.join(subdir_path, filename)
            
            restored_name = filename
            if remove_prefix_on_organize and separator_on_organize:
                # Attempt to restore prefix: category_name + separator + filename
                # This assumes category_name was the original prefix.
                # More sophisticated restoration might be needed if category names were sanitized.
                if category_name != "NO_SEPARATOR" and category_name != "UNNAMED_CATEGORY":
                     restored_name = f"{category_name}{separator_on_organize}{filename}"
            
            dst_path = os.path.join(directory, restored_name)

            try:
                if os.path.exists(dst_path):
                    # Handle conflict: append a number or skip
                    # For simplicity, we'll skip and log an error.
                    # A more robust solution might rename (e.g., file_1.txt, file_2.txt)
                    errors.append(f"Conflict: Target file '{dst_path}' already exists in main directory. Skipping '{filename}' from '{category_name}'.")
                    continue
                
                shutil.move(src_path, dst_path)
                moved_count += 1
            except Exception as e:
                errors.append(f"Error moving '{src_path}' to '{dst_path}': {e}")

        # After moving all files, check if subdirectory is empty and remove it
        try:
            if not os.listdir(subdir_path): # Check if directory is empty
                os.rmdir(subdir_path)
                removed_dirs_count += 1
            # else:
                # errors.append(f"Subdirectory '{subdir_path}' is not empty after moving files. Not removed.")
        except Exception as e:
            errors.append(f"Error removing directory '{subdir_path}': {e}")
            
    return moved_count, removed_dirs_count, errors

def generate_directory_tree(directory, output_file=None, show_hidden=False, max_depth=None):
    """
    Generates a tree-like representation of the directory structure.

    Args:
        directory (str): The path to the directory to analyze.
        output_file (str, optional): Path to save the tree structure. If None,
                                    returns the tree as a string. Defaults to None.
        show_hidden (bool, optional): Whether to include hidden files/folders.
                                     Defaults to False.
        max_depth (int, optional): Maximum depth to traverse. None for unlimited.
                                  Defaults to None.

    Returns:
        str: The tree structure as a string if output_file is None.
        None: If output_file is specified, saves to file and returns None.

    Raises:
        FileNotFoundError: If the directory doesn't exist.
        PermissionError: If there's no permission to access directory or write file.
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    def _build_tree(path, prefix="", depth=0, is_last=True):
        """Recursively builds the tree structure."""
        if max_depth is not None and depth > max_depth:
            return []
        
        lines = []
        base_name = os.path.basename(path)
        
        if depth == 0:
            lines.append(f"{base_name}/\n")
        else:
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{base_name}{'/' if os.path.isdir(path) else ''}\n")
        
        if os.path.isdir(path):
            try:
                items = os.listdir(path)
                if not show_hidden:
                    items = [item for item in items if not item.startswith('.')]
                
                # Sort: directories first, then files, both alphabetically
                dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
                files = [item for item in items if os.path.isfile(os.path.join(path, item))]
                sorted_items = sorted(dirs) + sorted(files)
                
                for i, item in enumerate(sorted_items):
                    item_path = os.path.join(path, item)
                    is_last_item = (i == len(sorted_items) - 1)
                    
                    if depth == 0:
                        next_prefix = ""
                    else:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                    
                    lines.extend(_build_tree(item_path, next_prefix, depth + 1, is_last_item))
                    
            except PermissionError:
                if depth > 0:
                    error_prefix = prefix + ("    " if is_last else "│   ")
                    lines.append(f"{error_prefix}[Permission Denied]\n")
        
        return lines

    tree_lines = _build_tree(directory)
    tree_content = "".join(tree_lines)
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(tree_content)
        except Exception as e:
            raise PermissionError(f"Could not write to file {output_file}: {e}")
        return None
    else:
        return tree_content

if __name__ == "__main__":
    target_dir = input("Enter directory path to organize: ").strip()
    if os.path.isdir(target_dir):
        separator = input("Enter file name separator (default is '-'): ").strip() or '-'
        categories = get_organization_plan(target_dir, separator)
        
        # Show organization plan
        print("\nOrganization Plan:")
        print("=" * 40)
        for category, files in categories.items():
            print(f"\nCategory: {category} (Directory: {category}/)")
            print(f"Files to move: {len(files)}")
            if len(files) > 5:
                print("  " + "\n  ".join(files[:3]) + f"\n  ...and {len(files)-3} more")
            else:
                print("  " + "\n  ".join(files))
        print("=" * 40)
        
        # Get user confirmation
        response = input("\nProceed with organization? (y/n): ").lower()
        if response != 'y':
            print("Operation cancelled.")
        else:
            remove_prefix = input("Remove file name prefixes? (y/n): ").lower() == 'y'
            moved_count, num_categories, errors = execute_organization(target_dir, categories, remove_prefix, separator)
            
            # Show summary
            print(f"\nSuccessfully moved {moved_count} files to {num_categories} directories")
            if errors:
                print("Errors:")
                for error in errors:
                    print(f" - {error}")
            print("Organization complete!")
    else:
        print("Error: Invalid directory path")