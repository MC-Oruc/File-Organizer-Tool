"""
File Organizer Tool - Main entry point

This script launches the graphical user interface for the File Organizer Tool,
or processes files via command-line interface if arguments are provided.
"""
import sys
import os
import argparse

# Ensure the project directory is in the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Moved imports here to be available for the main() function
import tkinter as tk
from gui_organizer import FileOrganizerApp
from file_organizer import get_organization_plan, execute_organization, reverse_organization_action, generate_directory_tree

def handle_cli_mode(args):
    """
    Process the file organization via command line interface.
    
    Args:
        args: The parsed command-line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    try:
        # Check if directory exists
        if not os.path.isdir(args.directory):
            print(f"Error: Directory not found: {args.directory}")
            return 1
            
        if args.export_tree:
            # Handle directory tree export
            output_file = args.output or f"{os.path.basename(args.directory)}_tree.txt"
            
            try:
                print(f"Generating directory tree for {args.directory}...")
                generate_directory_tree(args.directory, output_file, 
                                       show_hidden=args.show_hidden, 
                                       max_depth=args.max_depth)
                print(f"Directory tree saved to: {output_file}")
                return 0
            except Exception as e:
                print(f"Error generating directory tree: {e}")
                return 1
                
        if args.reverse:
            # Handle reverse organization
            print(f"Scanning subdirectories in {args.directory}...")
            
            # Build organized categories from existing subdirectories
            organized_categories = {}
            subdirs = [d for d in os.listdir(args.directory) 
                      if os.path.isdir(os.path.join(args.directory, d))]
            
            if not subdirs:
                print("No subdirectories found to reverse organization.")
                return 1
                
            for subdir in subdirs:
                subdir_path = os.path.join(args.directory, subdir)
                files = [f for f in os.listdir(subdir_path) 
                        if os.path.isfile(os.path.join(subdir_path, f))]
                if files:
                    organized_categories[subdir] = files
            
            if not organized_categories:
                print("No files found in subdirectories to move back.")
                return 1
                
            print(f"Found {sum(len(files) for files in organized_categories.values())} files in "
                  f"{len(organized_categories)} subdirectories.")
                  
            if not args.yes and input("Proceed with reversal? (y/n): ").lower() != 'y':
                print("Operation cancelled.")
                return 0
                
            moved_count, removed_dirs, errors = reverse_organization_action(
                args.directory, organized_categories, args.remove_prefix, args.separator)
                
            print(f"Successfully moved {moved_count} files back to the main directory.")
            if removed_dirs:
                print(f"Removed {removed_dirs} empty subdirectories.")
            if errors:
                print(f"Encountered {len(errors)} errors:")
                for error in errors[:5]:
                    print(f"  - {error}")
                if len(errors) > 5:
                    print(f"  - ... and {len(errors)-5} more errors.")
                return 1 if len(errors) == sum(len(files) for files in organized_categories.values()) else 0
                
        else:
            # Handle forward organization
            print(f"Analyzing files in {args.directory}...")
            categories = get_organization_plan(args.directory, args.separator)
            
            if not categories:
                print("No files found that can be organized.")
                return 1
                
            file_count = sum(len(files) for files in categories.values())
            print(f"Found {file_count} files in {len(categories)} categories.")
            
            # Show organization plan
            if args.verbose:
                for category, files in categories.items():
                    print(f"\nCategory: {category} ({len(files)} files)")
                    for file in files[:5]:
                        if args.remove_prefix and args.separator in file:
                            new_name = file.split(args.separator, 1)[1].strip()
                            print(f"  {file} -> {new_name}")
                        else:
                            print(f"  {file}")
                    if len(files) > 5:
                        print(f"  ... and {len(files)-5} more files")
                        
            if not args.yes and input("Proceed with organization? (y/n): ").lower() != 'y':
                print("Operation cancelled.")
                return 0
                
            moved_count, dir_count, errors = execute_organization(
                args.directory, categories, args.remove_prefix, args.separator)
                
            print(f"Successfully moved {moved_count} files to {dir_count} directories.")
            if errors:
                print(f"Encountered {len(errors)} errors:")
                for error in errors[:5]:
                    print(f"  - {error}")
                if len(errors) > 5:
                    print(f"  - ... and {len(errors)-5} more errors.")
                return 1 if len(errors) == file_count else 0
                
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def main():
    """
    Initializes and runs the File Organizer Application.
    This function serves as the entry point for both direct execution 
    and when installed via pip/setup.py.
    
    Determines whether to run in GUI or CLI mode based on command-line arguments.
    """
    parser = argparse.ArgumentParser(description='File Organizer Tool - Organize files into subdirectories based on filename prefixes.')
    parser.add_argument('directory', nargs='?', help='Directory containing files to organize (if not specified, GUI mode is launched)')
    parser.add_argument('-s', '--separator', default='-', help='Character that separates prefix from filename (default: -)')
    parser.add_argument('-r', '--remove-prefix', action='store_true', help='Remove the prefix from filenames when organizing')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed information about the operations')
    parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--reverse', action='store_true', help='Reverse a previous organization, moving files back from subdirectories')
    parser.add_argument('--export-tree', action='store_true', help='Export directory tree')
    parser.add_argument('--output', help='Output file for directory tree export')
    parser.add_argument('--show-hidden', action='store_true', help='Include hidden files and directories in directory tree')
    parser.add_argument('--max-depth', type=int, help='Maximum depth for directory tree generation')
    
    args = parser.parse_args()
    
    # If directory is provided, run in CLI mode
    if args.directory:
        return handle_cli_mode(args)
    else:
        # No arguments provided, run GUI mode
        root = tk.Tk()
        app = FileOrganizerApp(root)
        root.mainloop()
        return 0  # Return success code

# Import and start the GUI if executed directly
if __name__ == "__main__":
    sys.exit(main())
