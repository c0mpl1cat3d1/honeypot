import os
import sys
import importlib
import datetime

# ===== CONFIG =====
COMMANDS_FOLDER = "commands"
LOG_FILE = "logs/commands.log"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== STATE =====
current_directory = "/home/user"
username = "guest"
hostname = "honeypot"

# ===== LOGGING =====
def log_command(command):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()} - {command}\n")


# ===== LOAD COMMAND =====
def load_command(cmd):
    try:
        module = importlib.import_module(f"{COMMANDS_FOLDER}.{cmd}")
        return module
    except ModuleNotFoundError:
        return None


# ===== EXECUTE COMMAND =====
def execute_command(command):
    global current_directory

    parts = command.strip().split()
    if not parts:
        return

    cmd = parts[0]
    args = parts[1:]

    # Built-in commands
    if cmd == "cd":
        if args:
            current_directory = args[0]
        else:
            current_directory = "/home/user"
        return

    if cmd == "exit":
        print("logout")
        exit()

    # External commands
    module = load_command(cmd)
    if module:
        try:
            output = module.run(args, current_directory)
            if output:
                print(output)
        except Exception as e:
            print("Error executing command")
    else:
        print(f"{cmd}: command not found")


# ===== MAIN LOOP =====
def start_cli():
    while True:
        prompt = f"{username}@{hostname}:{current_directory}$ "
        try:
            command = input(prompt)

            log_command(command)
            execute_command(command)

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")


if __name__ == "__main__":
    start_cli()