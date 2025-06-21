"""
Main graphical user interface for the File Organizer Tool.

Allows users to select a directory, define organization parameters,
preview changes, and apply or reverse the file organization.
Supports multiple languages and UI themes.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from file_organizer import get_organization_plan, execute_organization, reverse_organization_action, generate_directory_tree # Import new reverse function and tree function
from localization import LocaleManager
import threading
# import shutil # No longer needed here for reverse, moved to file_organizer
import os
import subprocess
import sys
from collections import defaultdict
# import time # Not explicitly used, can be removed if _process_preview simulation is removed

class FileOrganizerApp:
    """
    The main application class for the File Organizer GUI.
    """
    def __init__(self, root):
        """
        Initializes the FileOrganizerApp.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.locale_manager = LocaleManager(locales_dir="locales", default_lang="en")

        # Store widgets that need text updates
        self.widgets_to_translate = {}

        self.root.geometry("900x650") # Increased height for language selector

        # --- Top Control Panel ---
        control_panel = ttk.Frame(root, padding="10")
        control_panel.pack(fill=tk.X)

        # Language Selection
        lang_frame = ttk.Frame(control_panel)
        lang_frame.pack(fill=tk.X, pady=(0,10))
        self.widgets_to_translate['lang_label'] = ttk.Label(lang_frame)
        self.widgets_to_translate['lang_label'].pack(side=tk.LEFT, padx=(0,5))
        
        self.lang_var = tk.StringVar(value=self.locale_manager.get_current_language_code())
        available_langs_display = self.locale_manager.get_available_languages_display()
        
        # Ensure that the list for Combobox values is just the codes, not the display names
        self.lang_codes = list(available_langs_display.keys())
        self.lang_display_names = [available_langs_display[code] for code in self.lang_codes]

        self.lang_combobox = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=self.lang_display_names, state="readonly")
        try: # Set initial selection based on display name
            current_lang_display_name = available_langs_display[self.locale_manager.get_current_language_code()]
            self.lang_combobox.set(current_lang_display_name)
        except KeyError:
            if self.lang_display_names:
                self.lang_combobox.set(self.lang_display_names[0]) # Fallback to first available
            
        self.lang_combobox.pack(side=tk.LEFT)
        self.lang_combobox.bind("<<ComboboxSelected>>", self.change_language)


        # Directory Selection Group
        self.widgets_to_translate['dir_group'] = ttk.LabelFrame(control_panel, padding="10")
        self.widgets_to_translate['dir_group'].pack(fill=tk.X, pady=5)

        dir_inner_frame = ttk.Frame(self.widgets_to_translate['dir_group'])
        dir_inner_frame.pack(fill=tk.X)

        self.widgets_to_translate['dir_label'] = ttk.Label(dir_inner_frame)
        self.widgets_to_translate['dir_label'].pack(side=tk.LEFT, padx=(0,5))
        self.dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_inner_frame, textvariable=self.dir_var)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets_to_translate['browse_button'] = ttk.Button(dir_inner_frame, command=self.browse_directory)
        self.widgets_to_translate['browse_button'].pack(side=tk.LEFT)

        # Options Group
        self.widgets_to_translate['options_group'] = ttk.LabelFrame(control_panel, padding="10")
        self.widgets_to_translate['options_group'].pack(fill=tk.X, pady=5)

        sep_frame = ttk.Frame(self.widgets_to_translate['options_group'])
        sep_frame.pack(fill=tk.X, pady=(0,5))
        self.widgets_to_translate['sep_label'] = ttk.Label(sep_frame)
        self.widgets_to_translate['sep_label'].pack(side=tk.LEFT, padx=(0,5))
        self.sep_var = tk.StringVar(value='-')
        sep_entry = ttk.Entry(sep_frame, textvariable=self.sep_var, width=5)
        sep_entry.pack(side=tk.LEFT, padx=5)
        self.widgets_to_translate['sep_tooltip'] = ttk.Label(sep_frame)
        self.widgets_to_translate['sep_tooltip'].pack(side=tk.LEFT, fill=tk.X, expand=True)

        prefix_frame = ttk.Frame(self.widgets_to_translate['options_group'])
        prefix_frame.pack(fill=tk.X)
        self.remove_prefix_var = tk.BooleanVar(value=False)
        self.widgets_to_translate['remove_prefix_checkbox'] = ttk.Checkbutton(prefix_frame,
                        variable=self.remove_prefix_var, command=self.on_option_change)
        self.widgets_to_translate['remove_prefix_checkbox'].pack(side=tk.LEFT, padx=(0,5))
        self.widgets_to_translate['remove_prefix_tooltip'] = ttk.Label(prefix_frame)
        self.widgets_to_translate['remove_prefix_tooltip'].pack(side=tk.LEFT, fill=tk.X, expand=True)

        preview_button_frame = ttk.Frame(root, padding=(0,0,0,5))
        preview_button_frame.pack(fill=tk.X)
        self.widgets_to_translate['preview_button'] = ttk.Button(preview_button_frame, command=self.preview_organization)
        self.widgets_to_translate['preview_button'].pack()

        self.progress = ttk.Progressbar(root, mode='indeterminate')

        paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.widgets_to_translate['current_frame'] = ttk.LabelFrame(paned_window)
        paned_window.add(self.widgets_to_translate['current_frame'], weight=1)
        
        self.widgets_to_translate['plan_frame'] = ttk.LabelFrame(paned_window)
        paned_window.add(self.widgets_to_translate['plan_frame'], weight=1)
        
        self.current_tree = self._create_tree(self.widgets_to_translate['current_frame'])
        self.plan_tree = self._create_tree(self.widgets_to_translate['plan_frame'])
        
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(root, padding="5")
        btn_frame.pack(fill=tk.X)
        self.widgets_to_translate['expand_all_button'] = ttk.Button(btn_frame, command=self.expand_all)
        self.widgets_to_translate['expand_all_button'].pack(side=tk.LEFT, padx=5, pady=5)
        self.widgets_to_translate['collapse_all_button'] = ttk.Button(btn_frame, command=self.collapse_all)
        self.widgets_to_translate['collapse_all_button'].pack(side=tk.LEFT, padx=5, pady=5)

        execute_button_frame = ttk.Frame(root, padding="5")
        execute_button_frame.pack(fill=tk.X)
        self.widgets_to_translate['apply_organization_button'] = ttk.Button(execute_button_frame, 
                                      command=self.execute_organization, state=tk.DISABLED)
        self.widgets_to_translate['apply_organization_button'].pack(side=tk.LEFT, padx=5, pady=5)
        
        self.widgets_to_translate['reverse_organization_button'] = ttk.Button(execute_button_frame, 
                                      command=self.reverse_organization)
        self.widgets_to_translate['reverse_organization_button'].pack(side=tk.LEFT, padx=5, pady=5)

        # Add Export Tree button
        self.widgets_to_translate['export_tree_button'] = ttk.Button(execute_button_frame,
                                      command=self.export_directory_tree)
        self.widgets_to_translate['export_tree_button'].pack(side=tk.LEFT, padx=5, pady=5)

        # Add an "Open Directory" button and keep it disabled until reverse is done
        self.open_dir_button = ttk.Button(execute_button_frame, 
                                          text="Open Directory",  # or localize as needed
                                          command=self.open_target_directory,
                                          state=tk.DISABLED)
        self.open_dir_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        self.categories = {}
        self.update_ui_texts() # Initial text setup

    def update_ui_texts(self):
        """Updates all translatable text elements in the GUI."""
        lm = self.locale_manager
        self.root.title(lm.get_string("window_title"))

        self.widgets_to_translate['lang_label'].config(text=lm.get_string("language_label"))
        self.widgets_to_translate['dir_group'].config(text=lm.get_string("source_directory_group"))
        self.widgets_to_translate['dir_label'].config(text=lm.get_string("directory_label"))
        self.widgets_to_translate['browse_button'].config(text=lm.get_string("browse_button"))
        
        self.widgets_to_translate['options_group'].config(text=lm.get_string("organization_options_group"))
        self.widgets_to_translate['sep_label'].config(text=lm.get_string("separator_char_label"))
        self.widgets_to_translate['sep_tooltip'].config(text=lm.get_string("separator_char_tooltip"))
        self.widgets_to_translate['remove_prefix_checkbox'].config(text=lm.get_string("remove_prefix_checkbox"))
        self.widgets_to_translate['remove_prefix_tooltip'].config(text=lm.get_string("remove_prefix_tooltip"))
        
        self.widgets_to_translate['preview_button'].config(text=lm.get_string("preview_button"))
        
        self.widgets_to_translate['current_frame'].config(text=lm.get_string("current_files_header"))
        self.widgets_to_translate['plan_frame'].config(text=lm.get_string("planned_organization_header"))
        
        self.current_tree.heading("#0", text=lm.get_string("tree_col_file_category"))
        self.current_tree.heading("count", text=lm.get_string("tree_col_file_count"))
        self.plan_tree.heading("#0", text=lm.get_string("tree_col_file_category")) # Plan tree might have different main col name
        self.plan_tree.heading("count", text=lm.get_string("tree_col_file_count"))

        self.widgets_to_translate['expand_all_button'].config(text=lm.get_string("expand_all_button"))
        self.widgets_to_translate['collapse_all_button'].config(text=lm.get_string("collapse_all_button"))
        self.widgets_to_translate['apply_organization_button'].config(text=lm.get_string("apply_organization_button"))
        self.widgets_to_translate['reverse_organization_button'].config(text=lm.get_string("reverse_organization_button"))
        self.widgets_to_translate['export_tree_button'].config(text=lm.get_string("export_tree_button"))
        
        # Update status bar if it has a generic message or re-evaluate its current message
        # For now, we assume status messages are set dynamically with translated strings.

    def change_language(self, event=None):
        """Handles language change from the combobox."""
        selected_display_name = self.lang_var.get()
        # Find the code corresponding to the selected display name
        selected_code = None
        for code, display_name in self.locale_manager.get_available_languages_display().items():
            if display_name == selected_display_name:
                selected_code = code
                break
        
        if selected_code:
            self.locale_manager.set_language(selected_code)
            self.update_ui_texts()
            # If there's data in the trees, re-render them without reopening dialog
            if self.dir_var.get():
                self.browse_directory(directory_path=self.dir_var.get())
            if self.categories:
                 self._update_preview(self.dir_var.get(), self.categories, True)
        else:
            print(f"Could not find code for display name: {selected_display_name}")


    def change_theme(self, event=None):
        """Handles theme change from the combobox."""
        selected_theme = self.theme_var.get()
        # Here you would implement the logic to change the application's theme
        # This is highly dependent on how themes are managed in your application
        # For now, let's just print the selected theme
        print(f"Selected theme: {selected_theme}")
        # You would typically apply the theme and then update the UI texts if necessary
        # For example:
        # apply_theme(selected_theme)
        # self.update_ui_texts()

    def _create_tree(self, parent):
        """
        Creates a ttk.Treeview widget with a scrollbar.

        Args:
            parent (ttk.Frame): The parent widget for the treeview.

        Returns:
            ttk.Treeview: The created treeview widget.
        """
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree = ttk.Treeview(tree_frame, columns=("count"), show="tree headings")
        tree.heading("#0", text="Dosya/Kategori")
        tree.heading("count", text="Dosya Sayısı")
        tree.column("#0", width=300, anchor=tk.W)
        tree.column("count", width=80, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        return tree
    
    def browse_directory(self, directory_path=None):
        """
        Handles directory selection. Populates the 'Current File Structure' tree.

        Args:
            directory_path (str, optional): If provided, uses this path instead
                                            of opening a dialog. Defaults to None.
        """
        if directory_path is None:  # If no path is provided, open the dialog
            directory = filedialog.askdirectory()
        else:
            directory = directory_path  # Use the provided path

        if directory:
            self.dir_var.set(directory)
            self.current_tree.delete(*self.current_tree.get_children())
            self.plan_tree.delete(*self.plan_tree.get_children())
            # self.execute_btn.config(state=tk.DISABLED) # Use translated key for button
            self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
            self.status_var.set(self.locale_manager.get_string("status_dir_selected", directory=directory))

            try:
                for item in self.current_tree.get_children():
                    self.current_tree.delete(item)
                files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
                if not files:
                     self.current_tree.insert("", tk.END, text=self.locale_manager.get_string("no_files_in_directory_placeholder"), open=True)
                else:
                    root_node = self.current_tree.insert("", tk.END, text=os.path.basename(directory), open=True)
                    for file in files:
                        self.current_tree.insert(root_node, tk.END, text=file, values=("",))
            except Exception as e:
                messagebox.showerror(self.locale_manager.get_string("error_title"), 
                                     self.locale_manager.get_string("error_updating_current_structure", error=str(e)))
                for item in self.current_tree.get_children():
                    self.current_tree.delete(item)

    def preview_organization(self):
        """Initiates the preview of the file organization plan."""
        directory = self.dir_var.get()
        if not directory:
            messagebox.showerror(self.locale_manager.get_string("error_title"), self.locale_manager.get_string("error_select_directory"))
            return
        
        separator = self.sep_var.get().strip() or '-'
        
        self.widgets_to_translate['preview_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.start()
        self.status_var.set(self.locale_manager.get_string("status_analyzing_files"))
        self.root.update_idletasks()
        
        threading.Thread(target=self._process_preview, args=(directory, separator), daemon=True).start()

    def _process_preview(self, directory, separator):
        """
        Processes file analysis in a separate thread for the preview.
        """
        # perform actual analysis without artificial delay
        try:
            categories = get_organization_plan(directory, separator)
            self.root.after(0, self._update_preview, directory, categories, False)
        except Exception as e:
            self.root.after(0, messagebox.showerror, self.locale_manager.get_string("error_title"), 
                            self.locale_manager.get_string("error_processing_preview", error=str(e)))
            self.root.after(0, self._reset_ui)

    def _update_preview(self, directory, categories, options_changed=False):
        """
        Updates the 'Planned Organization' treeview with the categories.
        Also updates the 'Current File Structure' tree if it's the first preview.

        Args:
            directory (str): The path of the directory being previewed.
            categories (dict): The categorized file data.
            options_changed (bool, optional): True if only options changed,
                                              not the directory or a new scan.
                                              Defaults to False.
        """
        lm = self.locale_manager
        if not options_changed:
            self.categories = categories
        
        self.plan_tree.delete(*self.plan_tree.get_children())
        remove_prefix = self.remove_prefix_var.get()
        separator = self.sep_var.get().strip() or '-'
        
        if not self.categories:
            self.plan_tree.insert("", tk.END, text=lm.get_string("plan_not_created_placeholder"), open=True)
        else:
            for category, files in self.categories.items():
                parent = self.plan_tree.insert("", tk.END, text=category, values=(len(files),), open=False)
                for file in files:
                    display_name = file
                    if remove_prefix and separator in file:
                        parts = file.split(separator, 1)
                        if len(parts) > 1: display_name = parts[1].strip()
                        else: display_name = ""
                    if not display_name:
                        display_name = lm.get_string("file_empty_after_prefix_removal", file=file)
                    self.plan_tree.insert(parent, tk.END, text=display_name, values=("",))
        
        if not self.current_tree.get_children() and not options_changed:
            try:
                for item in self.current_tree.get_children(): self.current_tree.delete(item)
                files_in_dir = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
                if not files_in_dir:
                     self.current_tree.insert("", tk.END, text=lm.get_string("no_files_in_directory_placeholder"), open=True)
                else:
                    root_node = self.current_tree.insert("", tk.END, text=os.path.basename(directory), open=True)
                    for file in files_in_dir: self.current_tree.insert(root_node, tk.END, text=file, values=("",))
            except Exception as e:
                messagebox.showerror(lm.get_string("error_title"), lm.get_string("error_updating_current_structure", error=str(e)))
                for item in self.current_tree.get_children(): self.current_tree.delete(item)

        self._reset_ui()
        if self.categories:
            self.widgets_to_translate['apply_organization_button'].config(state=tk.NORMAL)
            file_count = sum(len(f) for f in self.categories.values())
            self.status_var.set(lm.get_string("status_preview_generated", category_count=len(self.categories), file_count=file_count))
        else:
            self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
            self.status_var.set(lm.get_string("status_preview_failed"))

    def _reset_ui(self):
        """Resets UI elements like progress bar and button states after processing."""
        self.progress.stop()
        self.progress.pack_forget()
        self.widgets_to_translate['preview_button'].config(state=tk.NORMAL)
        self.widgets_to_translate['reverse_organization_button'].config(state=tk.NORMAL)
        # Apply button state depends on whether categories exist, so we don't reset it here

    def on_option_change(self):
        """
        Callback for when an organization option (like 'Remove Prefix') changes.
        Updates the preview if data already exists.
        """
        if self.categories and self.dir_var.get():
            self._update_preview(self.dir_var.get(), self.categories, True)

    def expand_all(self):
        """Expands all nodes in both treeviews."""
        for tree in [self.current_tree, self.plan_tree]:
            for child in tree.get_children(): tree.item(child, open=True)
    
    def collapse_all(self):
        """Collapses all nodes in both treeviews."""
        for tree in [self.current_tree, self.plan_tree]:
            for child in tree.get_children(): tree.item(child, open=False)

    def execute_organization(self):
        """Executes the file organization based on the current plan."""
        lm = self.locale_manager
        directory = self.dir_var.get()
        if not directory or not self.categories: return
        
        # Confirmation dialog needs to be translated too.
        if messagebox.askyesno(lm.get_string("success_title"), 
                           "Confirm Organization?"): # Placeholder message
            try:
                # Disable buttons and show progress
                self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
                self.widgets_to_translate['reverse_organization_button'].config(state=tk.DISABLED)
                self.widgets_to_translate['preview_button'].config(state=tk.DISABLED)
                self.progress.pack(fill=tk.X, padx=10, pady=5)
                self.progress.start()
                self.status_var.set(lm.get_string("status_analyzing_files"))
                self.root.update_idletasks()
                
                # Run the organization in a separate thread
                remove_prefix = self.remove_prefix_var.get()
                separator = self.sep_var.get().strip() or '-'
                
                threading.Thread(
                    target=self._execute_organization_thread,
                    args=(directory, self.categories, remove_prefix, separator),
                    daemon=True
                ).start()
            except Exception as e:
                self._reset_ui()
                messagebox.showerror(lm.get_string("error_title"), str(e))

    def _execute_organization_thread(self, directory, categories, remove_prefix, separator):
        """Processes file organization in a separate thread."""
        lm = self.locale_manager
        try:
            moved_count, dir_count, errors = execute_organization(
                directory, categories, remove_prefix=remove_prefix, separator=separator)
            
            # Use after() to safely update UI from the thread
            self.root.after(0, self._organization_complete, moved_count, dir_count, errors)
        except Exception as e:
            self.root.after(0, self._organization_error, str(e))

    def _organization_complete(self, moved_count, dir_count, errors):
        """Handle organization completion in the main thread."""
        lm = self.locale_manager
        self._reset_ui()
        
        # Result messages
        if errors:
            error_msg_str = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg_str += lm.get_string("and_x_more_errors", count_more=len(errors)-5)
            messagebox.showwarning(lm.get_string("partial_success_title"), 
                f"{lm.get_string('moved_files_to_dirs_message', moved_count=moved_count, dir_count=dir_count)}\n"
                f"{lm.get_string('x_errors_occurred', error_count=len(errors))}\n{error_msg_str}")
        else:
            messagebox.showinfo(lm.get_string("success_title"), 
                f"{lm.get_string('moved_files_to_dirs_message', moved_count=moved_count, dir_count=dir_count)}\n"
                f"{lm.get_string('organization_complete_message')}")
        
        self.status_var.set(lm.get_string("status_organization_complete", moved_count=moved_count))

    def _organization_error(self, error_message):
        """Handle organization error in the main thread."""
        lm = self.locale_manager
        self._reset_ui()
        messagebox.showerror(lm.get_string("error_title"), error_message)

    def reverse_organization(self):
        """Initiates the process to reverse a previous organization in the selected directory."""
        lm = self.locale_manager
        directory = self.dir_var.get()
        if not directory:
            messagebox.showerror(lm.get_string("error_title"), lm.get_string("error_select_directory"))
            return
        
        # Show progress during the initial directory scan
        self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['reverse_organization_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['preview_button'].config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.start()
        self.status_var.set(lm.get_string("status_scanning_dirs"))
        self.root.update_idletasks()
        
        # Run the directory scan in a background thread to prevent UI freezing
        threading.Thread(
            target=self._scan_directories_for_reverse,
            args=(directory,),
            daemon=True
        ).start()

    def _scan_directories_for_reverse(self, directory):
        """Scans directories in a background thread to find subdirectories for reversal."""
        lm = self.locale_manager
        try:
            subdirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
            self.root.after(0, self._process_subdirs_for_reverse, directory, subdirs)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._reset_ui)
            self.root.after(0, messagebox.showerror, 
                       lm.get_string("error_title"), 
                       lm.get_string("error_analyzing_for_reverse", error=error_msg))

    def _process_subdirs_for_reverse(self, directory, subdirs):
        """Processes the subdirectories after scanning."""
        lm = self.locale_manager
        self._reset_ui()
        
        if not subdirs:
            messagebox.showinfo(lm.get_string("info_title"), lm.get_string("error_no_subdirs_to_reverse"))
            return
        
        # Continue with the preview
        self._preview_reverse_operation(directory, subdirs)

    def _preview_reverse_operation(self, directory, subdirs):
        """
        Shows a confirmation dialog detailing the files to be moved back
        during a reverse operation.
        """
        lm = self.locale_manager
        
        # Show progress during file counting
        self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['reverse_organization_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['preview_button'].config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.start()
        self.status_var.set(lm.get_string("status_analyzing_files"))
        self.root.update_idletasks()
        
        # Run the file analysis in a background thread
        threading.Thread(
            target=self._analyze_files_for_reverse,
            args=(directory, subdirs),
            daemon=True
        ).start()

    def _analyze_files_for_reverse(self, directory, subdirs):
        """Analyzes files in subdirectories in a background thread."""
        lm = self.locale_manager
        try:
            # Just count the total files instead of building a detailed preview
            total_files_to_move = 0
            subdir_count = 0
            
            for subdir_name in subdirs:
                subdir_path = os.path.join(directory, subdir_name)
                try:
                    files_in_subdir = [f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))]
                    if files_in_subdir:
                        total_files_to_move += len(files_in_subdir)
                        subdir_count += 1
                except Exception as e:
                    print(f"Error scanning {subdir_name}: {str(e)}")
            
            # Update UI in the main thread with simplified information
            self.root.after(0, self._show_reverse_preview, directory, subdirs, total_files_to_move, subdir_count)
        except Exception as e:
            self.root.after(0, self._reset_ui)
            self.root.after(0, messagebox.showerror, 
                           lm.get_string("error_title"), 
                           lm.get_string("error_analyzing_for_reverse", error=str(e)))

    def _show_reverse_preview(self, directory, subdirs, total_files_to_move, subdir_count):
        """Shows a simplified reverse operation preview in the main thread."""
        lm = self.locale_manager
        self._reset_ui()
        
        if total_files_to_move == 0:
            messagebox.showinfo(lm.get_string("info_title"), lm.get_string("error_no_files_to_move_in_subdirs"))
            return
        
        # Simplified confirmation dialog
        result = messagebox.askyesno(
            lm.get_string("confirm_reverse_title"), 
            lm.get_string("confirm_reverse_simple", 
                         total_files=total_files_to_move, 
                         subdir_count=subdir_count),
            detail=lm.get_string("confirm_reverse_detail")
        )
        
        if result:
            self._execute_reverse_organization(directory, subdirs)

    def _execute_reverse_organization(self, directory, subdirs_to_process):
        """Executes the reverse organization by calling the backend function."""
        lm = self.locale_manager
        
        # Disable buttons and show progress
        self.widgets_to_translate['apply_organization_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['reverse_organization_button'].config(state=tk.DISABLED)
        self.widgets_to_translate['preview_button'].config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.start()
        self.status_var.set(lm.get_string("status_analyzing_files"))
        self.root.update_idletasks()
        
        # Build the organized_categories structure expected by the backend
        organized_categories_for_backend = defaultdict(list)
        for subdir_name in subdirs_to_process:
            subdir_path = os.path.join(directory, subdir_name)
            if os.path.isdir(subdir_path):
                try:
                    organized_categories_for_backend[subdir_name] = [
                        f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))
                    ]
                except Exception as e:
                    # Log error if a specific subdir can't be listed, but try to continue
                    messagebox.showwarning(lm.get_string("error_title"),
                                           lm.get_string("error_processing_subdir", subdir=subdir_name, error=str(e)))


        remove_prefix_setting_on_original_org = self.remove_prefix_var.get()
        separator_setting_on_original_org = self.sep_var.get().strip() or '-'

        # Run the reversal in a separate thread
        threading.Thread(
            target=self._execute_reverse_thread,
            args=(directory, organized_categories_for_backend, 
                  remove_prefix_setting_on_original_org, separator_setting_on_original_org),
            daemon=True
        ).start()

    def _execute_reverse_thread(self, directory, organized_categories, remove_prefix, separator):
        """Processes file reversal in a separate thread."""
        try:
            moved_count, removed_dirs_count, errors = reverse_organization_action(
                directory, organized_categories, remove_prefix, separator)
            
            # Use after() to safely update UI from the thread
            self.root.after(0, self._reversal_complete, directory, moved_count, removed_dirs_count, errors)
        except Exception as e:
            self.root.after(0, self._reversal_error, str(e))

    def _reversal_complete(self, directory, moved_count, removed_dirs_count, errors):
        """Handle reversal completion in the main thread."""
        lm = self.locale_manager
        self._reset_ui()
        
        result_msg = lm.get_string("reverse_moved_files_message", moved_count=moved_count)
        if removed_dirs_count > 0:
            result_msg += f"\n{lm.get_string('reverse_empty_dirs_deleted_message', empty_dir_count=removed_dirs_count)}"
        
        if errors:
            result_msg += f"\n{lm.get_string('reverse_errors_occurred_message', error_count=len(errors))}"
            error_details = "\n".join(errors[:5])
            if len(errors) > 5:
                error_details += lm.get_string("and_x_more_errors", count_more=len(errors)-5)
            messagebox.showwarning(lm.get_string("partial_success_title"), 
                                 f"{result_msg}\n\n{lm.get_string('x_errors_occurred', error_count=len(errors))}\n{error_details}")
        else:
            messagebox.showinfo(lm.get_string("success_title"), 
                          f"{result_msg}\n{lm.get_string('reverse_complete_message')}")
        
        self.browse_directory(directory_path=directory) # Refresh view
        self.status_var.set(lm.get_string("status_reverse_complete", moved_count=moved_count))
        self.open_dir_button.config(state=tk.NORMAL)

    def _reversal_error(self, error_message):
        """Handle reversal error in the main thread."""
        lm = self.locale_manager
        self._reset_ui()
        messagebox.showerror(lm.get_string("error_title"), 
                       f"An unexpected error occurred during reverse operation: {error_message}")

    def open_target_directory(self):
        """Opens the currently selected directory in the system's file explorer."""
        directory = self.dir_var.get()
        if directory and os.path.isdir(directory):
            # Use the appropriate command based on the operating system
            if sys.platform == "win32":
                os.startfile(directory)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", directory])
            else: # Assume Linux or other Unix-like OS
                subprocess.run(["xdg-open", directory])
        else:
            messagebox.showerror(self.locale_manager.get_string("error_title"), 
                                 self.locale_manager.get_string("error_invalid_directory", directory=directory))

    def export_directory_tree(self):
        """Exports the directory tree structure to a text file."""
        lm = self.locale_manager
        directory = self.dir_var.get()
        
        if not directory:
            messagebox.showerror(lm.get_string("error_title"), lm.get_string("error_select_directory"))
            return
        
        if not os.path.isdir(directory):
            messagebox.showerror(lm.get_string("error_title"), 
                               lm.get_string("error_invalid_directory", directory=directory))
            return
        
        # Ask user where to save the tree file
        default_filename = f"{os.path.basename(directory)}_tree.txt"
        output_file = filedialog.asksaveasfilename(
            title=lm.get_string("export_tree_save_title"),
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[
                (lm.get_string("txt_files"), "*.txt"),
                (lm.get_string("all_files"), "*.*")
            ]
        )
        
        if not output_file:
            return  # User cancelled
        
        # Show progress during export
        self.widgets_to_translate['export_tree_button'].config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.start()
        self.status_var.set(lm.get_string("status_generating_tree"))
        self.root.update_idletasks()
        
        # Run the export in a background thread
        threading.Thread(
            target=self._export_tree_thread,
            args=(directory, output_file),
            daemon=True
        ).start()

    def _export_tree_thread(self, directory, output_file):
        """Processes tree export in a separate thread."""
        lm = self.locale_manager
        try:
            generate_directory_tree(directory, output_file)
            self.root.after(0, self._export_tree_complete, output_file)
        except Exception as e:
            self.root.after(0, self._export_tree_error, str(e))

    def _export_tree_complete(self, output_file):
        """Handle tree export completion in the main thread."""
        lm = self.locale_manager
        self.progress.stop()
        self.progress.pack_forget()
        self.widgets_to_translate['export_tree_button'].config(state=tk.NORMAL)
        
        messagebox.showinfo(lm.get_string("success_title"), 
                          lm.get_string("export_tree_success", file=output_file))
        self.status_var.set(lm.get_string("status_tree_exported"))

    def _export_tree_error(self, error_message):
        """Handle tree export error in the main thread."""
        lm = self.locale_manager
        self.progress.stop()
        self.progress.pack_forget()
        self.widgets_to_translate['export_tree_button'].config(state=tk.NORMAL)
        
        messagebox.showerror(lm.get_string("error_title"), 
                           lm.get_string("error_exporting_tree", error=error_message))
        self.status_var.set("")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()
