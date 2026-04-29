import threading
import datetime
import uuid
import os
from core.filesystem import FileSystem
from core.cli import load_command


class Session:
    def __init__(self, connection, address):
        self.fs = FileSystem()

        self.conn = connection
        self.addr = address
        self.session_id = str(uuid.uuid4())[:8]

        # Session state
        self.username = "guest"
        self.hostname = "honeypot"
        self.current_directory = "/home/guest"

        # Logging
        self.log_file = f"logs/session_{self.session_id}.log"
        os.makedirs("logs", exist_ok=True)

        self.alive = True

    # ===== SEND DATA =====
    def send(self, data):
        try:
            self.conn.sendall(data.encode())
        except:
            self.alive = False

    # ===== RECEIVE DATA =====
    def receive(self):
        try:
            data = self.conn.recv(1024).decode().strip()
            return data
        except:
            self.alive = False
            return ""

    # ===== LOGGING =====
    def log(self, command):
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.datetime.now()} | {self.addr} | {command}\n")

    # ===== PROMPT =====
    def get_prompt(self):
        return f"{self.username}@{self.hostname}:{self.current_directory}$ "

    # ===== EXECUTION WRAPPER =====
    def run_command(self, command):
        # Modify CLI execution to work per session

        parts = command.strip().split()
        if not parts:
            return ""

        cmd = parts[0]
        args = parts[1:]

        # Built-in commands
        if cmd == "cd":
            if args:
                self.current_directory = args[0]
            else:
                self.current_directory = "/home/guest"
            return ""

        if cmd == "exit":
            self.alive = False
            return "logout\n"

        module = load_command(cmd)
        if module:
            try:
                output = module.run(args, self.current_directory)
                return (output + "\n") if output else ""
            except Exception as e:
                return f"Error executing command: {str(e)}\n"
        else:
            return f"{cmd}: command not found\n"

    # ===== MAIN SESSION LOOP =====
    def start(self):
        self.send("Welcome to Ubuntu 20.04 LTS\n")
        self.send("login successful\n\n")

        while self.alive:
            self.send(self.get_prompt())

            command = self.receive()
            if not command:
                break

            self.log(command)

            response = self.run_command(command)
            if response:
                self.send(response)

        self.conn.close()
        print(f"[+] Session closed: {self.session_id}")


# ===== THREAD HANDLER =====
def handle_client(connection, address):
    session = Session(connection, address)
    session.start()