import os
import shutil
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import json
import platform


class ImageSequenceCopier:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Sequence Copier")

        # Source directory label and button
        self.src_label = tk.Label(self.master, text="Source Directory:")
        self.src_label.grid(row=0, column=0, padx=5, pady=5)

        self.src_button = tk.Button(self.master, text="Select", command=self.select_src_dir)
        self.src_button.grid(row=0, column=1, padx=5, pady=5)

        self.src_dir_label = tk.Label(self.master, text="")
        self.src_dir_label.grid(row=0, column=2, padx=5, pady=5)

        # Output directory label and button
        self.out_label = tk.Label(self.master, text="Output Directory:")
        self.out_label.grid(row=1, column=0, padx=5, pady=5)

        self.out_button = tk.Button(self.master, text="Select", command=self.select_out_dir)
        self.out_button.grid(row=1, column=1, padx=5, pady=5)

        self.out_dir_label = tk.Label(self.master, text="")
        self.out_dir_label.grid(row=1, column=2, padx=5, pady=5)

        # Copy files and terminate buttons
        self.copy_button = tk.Button(self.master, text="Copy Files", command=self.copy_files)
        self.copy_button.grid(row=2, column=1, padx=5, pady=5)

        self.terminate_button = tk.Button(self.master, text="Terminate", command=self.terminate)
        self.terminate_button.grid(row=2, column=2, padx=5, pady=5)

        # Current directory label
        self.current_dir_label = tk.Label(self.master, text="")
        self.current_dir_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

        # Progress bars
        self.progress_frame = tk.Frame(self.master)
        self.progress_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        self.dir_progress_label = tk.Label(self.progress_frame, text="Current Step:")
        self.dir_progress_label.pack(side=tk.LEFT)

        self.dir_progress_var = tk.DoubleVar()
        self.dir_progress_bar = ttk.Progressbar(self.progress_frame, variable=self.dir_progress_var, maximum=100)
        self.dir_progress_bar.pack(side=tk.LEFT, padx=5)

        self.total_progress_label = tk.Label(self.progress_frame, text="Total Progress:")
        self.total_progress_label.pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, padx=5)

        self.src_dir = None
        self.out_dir = None

        self.terminate_flag = False

        if platform.system() == 'Windows':
            self.config_file = os.path.join(os.path.expanduser("~"), "BatchPreference.json")
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.preferences = json.load(f)
                    self.src_dir = self.preferences.get('src_dir')
                    self.out_dir = self.preferences.get('out_dir')
                    if self.src_dir:
                        self.src_dir_label.config(text=self.src_dir)
                    if self.out_dir:
                        self.out_dir_label.config(text=self.out_dir)
            else:
                self.preferences = {}
                with open(self.config_file, "w") as f:
                    json.dump(self.preferences, f)
        else:
            self.preferences = {}

    def select_src_dir(self):
        self.src_dir = filedialog.askdirectory()
        if self.src_dir:
            self.src_dir_label.config(text=self.src_dir)
            self.preferences['src_dir'] = self.src_dir
            with open(self.config_file, "w") as f:
                json.dump(self.preferences, f)

    def select_out_dir(self):
        self.out_dir = filedialog.askdirectory()
        if self.out_dir:
            self.out_dir_label.config(text=self.out_dir)
            self.preferences['out_dir'] = self.out_dir
            with open(self.config_file, "w") as f:
                json.dump(self.preferences, f)

    def copy_files(self):
        if self.src_dir is None or self.out_dir is None:
            return

        # Recursively get a list of all the files in the source directory
        files = []
        for root, dirs, filenames in os.walk(self.src_dir):
            for filename in filenames:
                files.append(os.path.join(root, filename))

        total_files = len(files)
        total_progress_step = 100 / total_files
        total_current_progress = 0

        # Copy each file to the output directory and rename it
        num_processed_in_dir = 0
        current_dir = ""
        frame_padding = 0
        dir_files = []
        for i, file in enumerate(files):
            if self.terminate_flag:
                return

            old_path = file
            relative_path = os.path.relpath(old_path, self.src_dir)
            new_path = os.path.join(self.out_dir, relative_path)

            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            if os.path.dirname(file) != current_dir:
                self.dir_progress_var.set(0)
                self.dir_progress_bar.update()
                dir_files = []
                num_processed_in_dir = 0
                current_dir = os.path.dirname(file)
                frame_padding = 0
                self.current_dir_label.config(text="Current directory: " + current_dir)

            filename, extension = os.path.splitext(os.path.basename(old_path))
            last_dot_pos = filename.rfind('.')
            new_frame_num = 1001 + num_processed_in_dir + frame_padding
            new_name = filename[:last_dot_pos] + '.' + str(new_frame_num).zfill(4) + extension
            new_file_path = os.path.join(os.path.dirname(new_path), new_name)

            try:
                shutil.copyfile(old_path, new_file_path)
            except shutil.SameFileError:
                pass

            total_current_progress += total_progress_step
            self.progress_var.set(total_current_progress)
            self.progress_bar.update()

            if os.path.isfile(new_file_path):
                dir_files.append(file)
                num_processed_in_dir += 1
                dir_progress = 100 * num_processed_in_dir / len(os.listdir(os.path.dirname(file)))
                self.dir_progress_var.set(dir_progress)
                self.dir_progress_bar.update()

        # Check number of files in destination directory matches source directory
        num_files_src = len(files)
        num_files_out = 0
        for root, dirs, filenames in os.walk(self.out_dir):
            num_files_out += len(filenames)
        if num_files_src == num_files_out:
            message = "Image sequence copied successfully."
        else:
            message = f"Error: expected {num_files_src} files, but got {num_files_out} files."
        self.current_dir_label.config(text="")
        tk.messagebox.showinfo("Copy Complete", message)

    def terminate(self):
        self.terminate_flag = True
        tk.messagebox.showinfo("Terminate", "The script has been terminated.")

if __name__ == '__main__':
    root = tk.Tk()
    app = ImageSequenceCopier(root)
    root.mainloop()
