class FileSystem:
    def __init__(self):
        self.fs = {
            "/": {
                "home": {
                    "guest": {
                        "notes.txt": "Meeting at 5PM\nDon't forget credentials\n",
                        "passwords.txt": "admin:admin123\nroot:toor\n"
                    }
                },
                "var": {
                    "log": {
                        "auth.log": "Failed login from 192.168.1.10\n"
                    }
                },
                "etc": {
                    "passwd": "root:x:0:0:root:/root:/bin/bash\n"
                }
            }
        }

    # ===== PATH RESOLVER =====
    def resolve_path(self, current_dir, path):
        if path.startswith("/"):
            full_path = path
        else:
            full_path = current_dir.rstrip("/") + "/" + path

        parts = [p for p in full_path.split("/") if p]
        node = self.fs["/"]

        for part in parts:
            if part in node:
                node = node[part]
            else:
                return None

        return node

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
            if path.startswith("/"):
                return path.rstrip("/") or "/"
            else:
                return (current_dir.rstrip("/") + "/" + path).replace("//", "/")
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