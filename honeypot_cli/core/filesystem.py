import json
import os
import posixpath


DEFAULT_FILESYSTEM = {
    "/": {
        "home": {
            "iiitr": {
                "notes.txt": "Meeting at 5PM\nDon't forget credentials\n",
                "passwords.txt": "admin:admin123\nroot:toor\n",
            },
            "guest": {
                "notes.txt": "Meeting at 5PM\nDon't forget credentials\n",
                "passwords.txt": "admin:admin123\nroot:toor\n",
            },
        },
        "var": {
            "log": {
                "auth.log": "Failed login from 192.168.1.10\n",
            }
        },
        "etc": {
            "passwd": "root:x:0:0:root:/root:/bin/bash\n",
        },
    }
}


class FileSystem:
    def __init__(self, json_path=None):
        self.json_path = json_path or self.default_json_path()
        self.fs = self.load_filesystem(self.json_path)

    @staticmethod
    def default_json_path():
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "data", "filesystem.json")

    @staticmethod
    def load_filesystem(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return DEFAULT_FILESYSTEM

        if not isinstance(data, dict) or "/" not in data or not isinstance(data["/"], dict):
            return DEFAULT_FILESYSTEM

        return data

    def save(self):
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.fs, f, indent=2)
            f.write("\n")

    # ===== PATH RESOLVER =====
    def resolve_path(self, current_dir, path):
        full_path = self.normalize_path(current_dir, path)
        parts = [p for p in full_path.split("/") if p]
        node = self.fs["/"]

        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]

        return node

    # ===== PATH NORMALIZER =====
    def normalize_path(self, current_dir, path):
        if not path or path == ".":
            full_path = current_dir
        elif path.startswith("/"):
            full_path = path
        else:
            full_path = posixpath.join(current_dir, path)

        full_path = posixpath.normpath(full_path)
        if not full_path.startswith("/"):
            full_path = "/" + full_path

        return full_path

    # ===== LIST DIRECTORY =====
    def ls(self, current_dir):
        node = self.resolve_path(current_dir, ".")
        if isinstance(node, dict):
            return "  ".join(node.keys())
        return "Not a directory"

    # ===== CHANGE DIRECTORY =====
    def cd(self, current_dir, path):
        node = self.resolve_path(current_dir, path)

        if isinstance(node, dict):
            return self.normalize_path(current_dir, path)
        return current_dir

    # ===== PRINT WORKING DIR =====
    def pwd(self, current_dir):
        return current_dir

    # ===== READ FILE =====
    def cat(self, current_dir, filename):
        node = self.resolve_path(current_dir, filename)

        if isinstance(node, str):
            return node
        return "No such file"

    # ===== CHECK EXISTS =====
    def exists(self, current_dir, path):
        return self.resolve_path(current_dir, path) is not None

    # ===== CREATE FILE =====
    def touch(self, current_dir, path):
        full_path = self.normalize_path(current_dir, path)
        parent_path = posixpath.dirname(full_path)
        filename = posixpath.basename(full_path)

        if not filename:
            return False, f"touch: cannot touch '{path}': No such file or directory"

        parent = self.resolve_path("/", parent_path)
        if parent is None:
            return False, f"touch: cannot touch '{path}': No such file or directory"
        if not isinstance(parent, dict):
            return False, f"touch: cannot touch '{path}': Not a directory"

        existing = parent.get(filename)
        if isinstance(existing, dict):
            return False, f"touch: cannot touch '{path}': Is a directory"

        if existing is None:
            parent[filename] = ""
            self.save()

        return True, ""

    # ===== WRITE FILE =====
    def write_file(self, current_dir, path, content=""):
        full_path = self.normalize_path(current_dir, path)
        parent_path = posixpath.dirname(full_path)
        filename = posixpath.basename(full_path)

        if not filename:
            return False, f"cannot write '{path}': No such file or directory"

        parent = self.resolve_path("/", parent_path)
        if parent is None:
            return False, f"cannot write '{path}': No such file or directory"
        if not isinstance(parent, dict):
            return False, f"cannot write '{path}': Not a directory"
        if isinstance(parent.get(filename), dict):
            return False, f"cannot write '{path}': Is a directory"

        parent[filename] = content
        self.save()
        return True, ""

    # ===== MAKE DIRECTORY =====
    def mkdir(self, current_dir, path):
        full_path = self.normalize_path(current_dir, path)
        parent_path = posixpath.dirname(full_path)
        dirname = posixpath.basename(full_path)

        if not dirname:
            return False, f"cannot create directory '{path}': File exists"

        parent = self.resolve_path("/", parent_path)
        if parent is None:
            return False, f"cannot create directory '{path}': No such file or directory"
        if not isinstance(parent, dict):
            return False, f"cannot create directory '{path}': Not a directory"
        if dirname in parent:
            return False, f"cannot create directory '{path}': File exists"

        parent[dirname] = {}
        self.save()
        return True, ""

    # ===== REMOVE FILE =====
    def remove(self, current_dir, path, recursive=False, force=False):
        full_path = self.normalize_path(current_dir, path)
        parent_path = posixpath.dirname(full_path)
        filename = posixpath.basename(full_path)

        if not filename:
            if force:
                return True, ""
            return False, f"rm: cannot remove '{path}': No such file or directory"

        parent = self.resolve_path("/", parent_path)
        if parent is None or not isinstance(parent, dict) or filename not in parent:
            if force:
                return True, ""
            return False, f"rm: cannot remove '{path}': No such file or directory"

        node = parent[filename]
        if isinstance(node, dict) and not recursive:
            return False, f"rm: cannot remove '{path}': Is a directory"

        del parent[filename]
        self.save()
        return True, ""
