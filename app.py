import tkinter as tk
from tkinter import messagebox
import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

TASKS_FILE = "tasks.json"

class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List")

        self.tasks = self.load_tasks()

        self.entry = tk.Entry(self.root, width=40)
        self.entry.pack(pady=10)

        self.add_button = tk.Button(self.root, text="Add Task", command=self.add_task)
        self.add_button.pack()

        self.listbox = tk.Listbox(self.root, width=50, height=10)
        self.listbox.pack(pady=10)

        self.delete_button = tk.Button(self.root, text="Delete Task", command=self.delete_task)
        self.delete_button.pack()

        self.refresh_list()

    def load_tasks(self):
        if not os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "w") as f:
                json.dump([], f)
            return []
        try:
            with open(TASKS_FILE, "r") as file:
                content = file.read().strip()
                if not content:
                    return []
                tasks = json.loads(content)
                return tasks if isinstance(tasks, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_tasks(self):
        with open(TASKS_FILE, "w") as file:
            json.dump(self.tasks, file, indent=4)

    def add_task(self):
        task_text = self.entry.get().strip()
        if not task_text:
            messagebox.showwarning("Warning", "Task cannot be empty!")
            return
        self.tasks.append({"task": task_text})
        self.save_tasks()
        self.entry.delete(0, tk.END)
        self.refresh_list()

    def delete_task(self):
        try:
            selected_index = self.listbox.curselection()[0]
            del self.tasks[selected_index]
            self.save_tasks()
            self.refresh_list()
        except IndexError:
            messagebox.showwarning("Warning", "Please select a task to delete!")

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for task in self.tasks:
            self.listbox.insert(tk.END, task["task"])


# ---------------- Web Server ------------------
class MyHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/save_tasks":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers["Content-Length"])
        post_data = json.loads(self.rfile.read(content_length))
        print("Received POST data:", post_data)

        if not os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "w") as f:
                json.dump([], f)

        try:
            with open(TASKS_FILE, "r") as file:
                tasks = json.load(file)
        except json.JSONDecodeError:
            tasks = []

        if post_data["action"] == "add":
            tasks.append({"task": post_data["task"]})
        elif post_data["action"] == "delete":
            if 0 <= post_data["index"] < len(tasks):
                del tasks[post_data["index"]]

        with open(TASKS_FILE, "w") as file:
            json.dump(tasks, file, indent=4)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode())


def start_server():
    PORT = 5500
    server = HTTPServer(("localhost", PORT), MyHandler)
    print(f"Server running at http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    root.mainloop()
