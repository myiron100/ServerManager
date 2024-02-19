import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess
import requests

class MinecraftServerManager:
    def __init__(self, root):
        self.root = root
        self.servers = {}
        self.server_frames = []
        self.init_ui()

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

    def add_server_to_ui(self, server_name):
        server_frame = tk.Frame(self.servers_frame, borderwidth=1, relief=tk.SUNKEN)
        server_frame.pack(pady=5, padx=5, fill=tk.X)

        server_label = tk.Label(server_frame, text=server_name)
        server_label.pack(side=tk.LEFT, padx=5)

        start_button = tk.Button(server_frame, text="Start", command=lambda: self.start_server(server_name))
        start_button.pack(side=tk.RIGHT, padx=5)

        self.server_frames.append(server_frame)


    def create_server(self):
        self.create_server_window = tk.Toplevel(self.root)
        self.create_server_window.title("Create a New Server")

        # Options pour le type de serveur
        self.server_type_var = tk.StringVar(value="Paper")
        tk.Radiobutton(self.create_server_window, text="Paper", variable=self.server_type_var, value="Paper").pack(anchor=tk.W)
        tk.Radiobutton(self.create_server_window, text="Magma", variable=self.server_type_var, value="Magma").pack(anchor=tk.W)

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
        server_type = self.server_type_var.get()
        version = self.server_version_var.get()
        server_name = self.server_name_var.get()

        if not server_name or not version:
            messagebox.showerror("Error", "Please enter both server name and version.")
            return
        
        


        # Construire l'URL de téléchargement en fonction du type et de la version
        if server_type == "Paper":
            url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/138/downloads/paper-{version}-138.jar"
        elif server_type == "Magma":
            # URL exemple pour Magma, peut nécessiter une mise à jour selon la structure exacte de leur API
            url = f"https://git.magmafoundation.org/api/v4/projects/5/packages/maven/org/magmafoundation/Magma/{version}/latest/Magma-{version}-latest-server.jar"
        else:
            messagebox.showerror("Error", "Invalid server type.")
            return

        server_folder = os.path.join(os.getenv('APPDATA'), 'MSM', server_name)
        os.makedirs(server_folder, exist_ok=True)
        
        jar_file = os.path.join(server_folder, f"{server_name}.jar")

        try:
            response = requests.get(url)
            with open(jar_file, 'wb') as file:
                file.write(response.content)
            self.servers[server_name] = {"folder": server_folder, "jar": jar_file}
            self.add_server_to_ui(server_name)
            self.create_server_window.destroy()
            messagebox.showinfo("Success", f"Server '{server_name}' created successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download and create the server: {e}")


    

    def start_server(self, server_name):
        server_info = self.servers.get(server_name)
        if server_info:
            jar_path = server_info["jar"]
            folder_path = server_info["folder"]

            # Définir les valeurs de RAM ici
            xms = "1024M"
            xmx = "1024M"

            # Lancer le processus du serveur
            self.process = subprocess.Popen(["java", "-Xms" + xms, "-Xmx" + xmx, "-jar", jar_path], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, stdin=subprocess.PIPE)

            # Créer une nouvelle fenêtre pour la console du serveur
            console_window = tk.Toplevel(self.root)
            console_window.title(f"Console - {server_name}")
            console_text = tk.Text(console_window, height=10)
            console_text.pack(fill=tk.BOTH, expand=True)

            # Zone de texte pour entrer des commandes
            command_entry = tk.Entry(console_window)
            command_entry.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

            # Fonction pour envoyer des commandes
            def send_command(event=None):
                command = command_entry.get()
                if command:
                    self.process.stdin.write(command + "\n")
                    self.process.stdin.flush()
                    command_entry.delete(0, tk.END)

            # Associer la fonction d'envoi de commande à la zone de texte
            command_entry.bind("<Return>", send_command)

            # Fonction pour mettre à jour la console
            def update_console():
                while True:
                    line = self.process.stdout.readline()
                    if line:
                        console_text.insert(tk.END, line)
                    else:
                        break

            # Lancer un thread pour lire les sorties du serveur
            thread = threading.Thread(target=update_console)
            thread.start()

            # Cadre pour les boutons
            buttons_frame = tk.Frame(console_window)
            buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)

            # Bouton pour arrêter le serveur
            stop_button = tk.Button(buttons_frame, text="Stop", command=lambda: self.stop_server(server_name, console_window, self.process))
            stop_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def stop_server(self, server_name, console_window, process):
        process.terminate()  # Arrêter le processus du serveur
        console_window.destroy()  # Fermer la fenêtre de la console
        messagebox.showinfo("Server Stopped", f"Server '{server_name}' has been stopped.")

# Create the main window and start the application
root = tk.Tk()
app = MinecraftServerManager(root)
root.mainloop()
