import os
import sys
import importlib
import importlib.util
import datetime
import inspect

# ===== CONFIG =====
COMMANDS_PACKAGE = "commands"
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
    if not cmd.isidentifier():
        return None

    module_name = f"{COMMANDS_PACKAGE}.{cmd}"
    if importlib.util.find_spec(module_name) is None:
        return None

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        if e.name == module_name:
            return None
        raise


def run_command_module(module, args, current_directory, context=None):
    """Run a command script, supporting optional session context."""
    run_func = module.run
    params = inspect.signature(run_func).parameters

    if len(params) >= 3:
        return run_func(args, current_directory, context or {})

    return run_func(args, current_directory)


def normalize_command_result(result, current_directory):
    """Convert command script results into output/session state."""
    if isinstance(result, dict):
        return {
            "output": result.get("output", "") or "",
            "current_directory": result.get("current_directory", current_directory),
            "exit": bool(result.get("exit", False)),
        }

    return {
        "output": result or "",
        "current_directory": current_directory,
        "exit": False,
    }


def run_external_command(cmd, args, current_directory, context=None):
    module = load_command(cmd)
    if not module:
        return None

    result = run_command_module(module, args, current_directory, context)
    return normalize_command_result(result, current_directory)


# ===== EXECUTE COMMAND =====
def execute_command(command):
    global current_directory

    parts = command.strip().split()
    if not parts:
        return

    cmd = parts[0]
    args = parts[1:]

    try:
        result = run_external_command(
            cmd,
            args,
            current_directory,
            {"username": username, "home_directory": "/home/user"},
        )
    except Exception:
        print("Error executing command")
        return

    if result:
        current_directory = result["current_directory"]
        if result["output"]:
            print(result["output"])
        if result["exit"]:
            print("logout")
            exit()
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
