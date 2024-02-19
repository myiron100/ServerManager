import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess
import requests
import json

class MinecraftServerManager:
    def __init__(self, root):
        self.root = root
        self.servers = {}
        self.server_frames = {}
        self.init_ui()
        self.load_servers()

    def init_ui(self):
        self.root.title("Minecraft Server Manager")
        self.root.geometry("600x400")

        self.add_server_button = tk.Button(self.root, text="Add New Server", command=self.add_server)
        self.add_server_button.pack(pady=10)

        self.create_server_button = tk.Button(self.root, text="Create a Server", command=self.create_server)
        self.create_server_button.pack(pady=10)

        self.servers_frame = tk.Frame(self.root)
        self.servers_frame.pack(fill=tk.BOTH, expand=True)

    def add_server(self):
        folder_path = filedialog.askdirectory(title="Select Server Folder")
        if folder_path:
            jar_file = filedialog.askopenfilename(title="Select Server JAR File", filetypes=[("JAR Files", "*.jar")])
            if jar_file:
                server_name = os.path.basename(folder_path)
                self.servers[server_name] = {"folder": folder_path, "jar": jar_file}
                self.add_server_to_ui(server_name)
                self.save_servers()

    def add_server_to_ui(self, server_name):
        server_frame = tk.Frame(self.servers_frame, borderwidth=1, relief=tk.SUNKEN)
        server_frame.pack(pady=5, padx=5, fill=tk.X)

        server_label = tk.Label(server_frame, text=server_name)
        server_label.pack(side=tk.LEFT, padx=5)

        start_button = tk.Button(server_frame, text="Start", command=lambda: self.start_server(server_name))
        start_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(server_frame, text="Delete", command=lambda: self.delete_server(server_name))
        delete_button.pack(side=tk.RIGHT, padx=5)

        self.server_frames[server_name] = server_frame

    def create_server(self):
        self.create_server_window = tk.Toplevel(self.root)
        self.create_server_window.title("Create a New Server")

        # Options pour la version du serveur
        self.server_version_var = tk.StringVar()
        self.server_version_entry = tk.Entry(self.create_server_window, textvariable=self.server_version_var)
        self.server_version_entry.pack(fill=tk.X, padx=5, pady=5)

        # Entrée pour le nom du serveur
        self.server_name_var = tk.StringVar()
        self.server_name_entry = tk.Entry(self.create_server_window, textvariable=self.server_name_var)
        self.server_name_entry.pack(fill=tk.X, padx=5, pady=5)

        create_button = tk.Button(self.create_server_window, text="Create Server", command=self.download_and_create_server)
        create_button.pack(pady=10)

def download_and_create_server(self):
    version = self.server_version_var.get()
    server_name = self.server_name_var.get()

    if not server_name or not version:
        messagebox.showerror("Error", "Please enter both server name and version.")
        return

    # Construisez l'URL correctement basé sur la documentation de l'API PaperMC
    url = f"https://papermc.io/api/v2/projects/paper/versions/{version}/builds/latest/downloads/paper-{version}-latest.jar"

    server_folder = os.path.join(os.getcwd(), 'MinecraftServerManager', server_name)
    os.makedirs(server_folder, exist_ok=True)

    jar_file = os.path.join(server_folder, f"{server_name}.jar")

    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(jar_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            self.servers[server_name] = {"folder": server_folder, "jar": jar_file}
            self.add_server_to_ui(server_name)
            self.save_servers()
            self.create_server_window.destroy()
            messagebox.showinfo("Success", f"Server '{server_name}' created successfully.")
        else:
            messagebox.showerror("Error", f"Failed to download the server JAR. The server version might be incorrect or not available.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download and create the server: {e}")


    def start_server(self, server_name):
        server_info = self.servers.get(server_name)
        if server_info:
            jar_path = server_info["jar"]
            folder_path = server_info["folder"]
            xms = "1024M"
            xmx = "1024M"
            self.process = subprocess.Popen(["java", "-Xms" + xms, "-Xmx" + xmx, "-jar", jar_path], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, stdin=subprocess.PIPE)
            console_window = tk.Toplevel(self.root)
            console_window.title(f"Console - {server_name}")
            console_text = tk.Text(console_window, height=10)
            console_text.pack(fill=tk.BOTH, expand=True)
            command_entry = tk.Entry(console_window)
            command_entry.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
            def send_command(event=None):
                command = command_entry.get()
                if command:
                    self.process.stdin.write(command + "\n")
                    self.process.stdin.flush()
                    command_entry.delete(0, tk.END)
            command_entry.bind("<Return>", send_command)
            def update_console():
                while True:
                    line = self.process.stdout.readline()
                    if line:
                        console_text.insert(tk.END, line)
                    else:
                        break
            thread = threading.Thread(target=update_console)
            thread.start()
            stop_button = tk.Button(console_window, text="Stop", command=lambda: self.stop_server(server_name, console_window, self.process))
            stop_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def delete_server(self, server_name):
        if messagebox.askyesno("Delete Server", f"Are you sure you want to delete '{server_name}'?"):
            # Attempt to delete server directory
            try:
                os.rmdir(self.servers[server_name]['folder'])
            except OSError as e:
                messagebox.showerror("Error", "Failed to delete server folder. Please ensure it is empty and try again.")
                return

            # Remove from UI and internal storage
            self.server_frames[server_name].destroy()
            del self.servers[server_name]
            del self.server_frames[server_name]
            self.save_servers()

    def stop_server(self, server_name, console_window, process):
        process.terminate()
        console_window.destroy()
        messagebox.showinfo("Server Stopped", f"Server '{server_name}' has been stopped.")

    def load_servers(self):
        try:
            with open('servers.json', 'r') as file:
                self.servers = json.load(file)
            for server_name in self.servers.keys():
                self.add_server_to_ui(server_name)
        except FileNotFoundError:
            self.servers = {}

    def save_servers(self):
        with open('servers.json', 'w') as file:
            json.dump(self.servers, file, indent=4)

root = tk.Tk()
app = MinecraftServerManager(root)
root.mainloop()


