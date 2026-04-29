import paramiko
import os
import threading
import socket
import datetime
import time
from paramiko import ServerInterface
from core.cli import run_external_command


class SSHShellHandler:
    """Handles SSH shell interactions"""
    
    def __init__(self, channel, username):
        self.channel = channel
        self.username = username
        self.current_directory = "/home/guest"
        self.hostname = "honeypot"
        self.log_file = f"logs/ssh_{os.getpid()}.log"
        os.makedirs("logs", exist_ok=True)
    
    def log_command(self, command):
        """Log command to file"""
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.datetime.now()} | {self.username} | {command}\n")
    
    def get_prompt(self):
        """Get the shell prompt"""
        return f"{self.username}@{self.hostname}:{self.current_directory}$ "

    def send_text(self, text):
        """Send terminal text using CRLF line endings."""
        self.channel.send(text.replace("\n", "\r\n").encode())
    
    def run_command(self, command):
        """Execute a command"""
        parts = command.strip().split()
        if not parts:
            return ""
        
        cmd = parts[0]
        args = parts[1:]
        
        try:
            result = run_external_command(
                cmd,
                args,
                self.current_directory,
                {
                    "username": self.username,
                    "hostname": self.hostname,
                    "home_directory": "/home/guest",
                },
            )
        except Exception as e:
            return f"Error: {str(e)}"

        if not result:
            return f"{cmd}: command not found"

        self.current_directory = result["current_directory"]
        if result["exit"]:
            return None  # Signal to close

        return result["output"]
    
    def handle_shell(self):
        """Handle interactive shell"""
        try:
            # Send banner
            self.send_text("Welcome to Ubuntu 20.04 LTS\n")
            self.send_text("login successful\n\n")
            self.send_text(self.get_prompt())

            buffer = ""
            
            while True:
                # SSH clients send raw keystrokes for interactive shells. Echo
                # printable input and process editing keys like a simple TTY.
                try:
                    data = self.channel.recv(1024)
                    if not data:
                        break
                except:
                    break

                text = data.decode("utf-8", errors="ignore")
                i = 0

                while i < len(text):
                    char = text[i]

                    if char == "\x03":  # Ctrl-C
                        buffer = ""
                        self.send_text("^C\n")
                        self.send_text(self.get_prompt())
                    elif char == "\x04":  # Ctrl-D
                        self.send_text("logout\n")
                        return
                    elif char in ("\r", "\n"):
                        if char == "\r" and i + 1 < len(text) and text[i + 1] == "\n":
                            i += 1

                        self.send_text("\n")
                        command = buffer.strip()
                        buffer = ""

                        if not command:
                            self.send_text(self.get_prompt())
                            i += 1
                            continue

                        self.log_command(command)

                        result = self.run_command(command)
                        if result is None:
                            self.send_text("logout\n")
                            return

                        if result:
                            self.send_text(result + "\n")

                        self.send_text(self.get_prompt())
                    elif char in ("\x7f", "\b"):  # Backspace/Delete
                        if buffer:
                            buffer = buffer[:-1]
                            self.channel.send(b"\b \b")
                    elif char == "\x1b":
                        # Ignore escape sequences such as arrow keys.
                        if i + 1 < len(text) and text[i + 1] == "[":
                            i += 2
                            while i < len(text) and not text[i].isalpha() and text[i] != "~":
                                i += 1
                        else:
                            self.channel.send(b"^[[")
                    elif char >= " " and char != "\x7f":
                        buffer += char
                        self.channel.send(char.encode())

                    i += 1
        
        except Exception as e:
            print(f"[Shell Error] {e}")
        finally:
            self.channel.close()


class SSHServerInterface(ServerInterface):
    """SSH Server implementation for honeypot"""
    
    def __init__(self):
        self.username = None
        self.password = None
    
    # ===== AUTHENTICATION =====
    def check_auth_password(self, username, password):
        """Accept any password for logging purposes"""
        self.username = username
        self.password = password
        print(f"[SSH-AUTH] {username}:{password}")
        return paramiko.AUTH_SUCCESSFUL
    
    def check_auth_publickey(self, username, key):
        """Accept any public key"""
        self.username = username
        print(f"[SSH-AUTH] {username} with public key")
        return paramiko.AUTH_SUCCESSFUL
    
    def get_allowed_auths(self, username):
        """List allowed auth methods"""
        return "password,publickey"
    
    # ===== CHANNEL SUPPORT =====
    def check_channel_request(self, kind, chanid):
        """Accept channel requests"""
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(
        self,
        channel,
        term,
        width,
        height,
        pixelwidth,
        pixelheight,
        modes,
    ):
        """Accept PTY requests from interactive SSH clients."""
        return True
    
    def check_channel_shell_request(self, channel):
        """Accept shell channel requests"""
        # Create handler and run in thread
        handler = SSHShellHandler(channel, self.username or "guest")
        thread = threading.Thread(target=handler.handle_shell, daemon=False)
        thread.start()
        return True

    def check_channel_exec_request(self, channel, command):
        """Accept one-shot commands like: ssh user@host ls."""
        if isinstance(command, bytes):
            command = command.decode("utf-8", errors="ignore")

        handler = SSHShellHandler(channel, self.username or "guest")

        def run_exec():
            try:
                handler.log_command(command)
                result = handler.run_command(command)

                if result is None:
                    channel.send(b"logout\n")
                elif result:
                    channel.send((result + "\n").encode())

                channel.send_exit_status(0)
            except Exception as e:
                print(f"[Exec Error] {e}")
                try:
                    channel.send_exit_status(1)
                except Exception:
                    pass
            finally:
                channel.close()

        thread = threading.Thread(target=run_exec, daemon=False)
        thread.start()
        return True


def start_ssh_server(host="0.0.0.0", port=2222, hostkey_path="core/ssh_host_key"):
    """Start SSH honeypot server"""
    
    # Ensure core directory exists
    os.makedirs(os.path.dirname(hostkey_path) if os.path.dirname(hostkey_path) else ".", exist_ok=True)
    
    # Generate or load host key
    if not os.path.exists(hostkey_path):
        print("[+] Generating SSH host key...")
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(hostkey_path)
        print(f"[+] Host key saved to {hostkey_path}")
    else:
        print(f"[+] Loading host key from {hostkey_path}")
    
    host_key = paramiko.RSAKey(filename=hostkey_path)
    
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)
    
    print(f"[+] SSH Honeypot running on {host}:{port}")
    
    try:
        while True:
            client, addr = sock.accept()
            print(f"[+] SSH Connection from {addr}")
            
            def handle_connection(c, a):
                try:
                    # Create SSH transport
                    transport = paramiko.Transport(c)
                    transport.add_server_key(host_key)
                    
                    server = SSHServerInterface()
                    
                    # Start server - this will handle all channel requests
                    transport.start_server(server=server)
                    
                    # Keep the transport alive while Paramiko handles channel requests.
                    while transport.is_active():
                        time.sleep(0.1)
                
                except Exception as e:
                    print(f"[SSH Error] {e}")
                finally:
                    try:
                        c.close()
                    except:
                        pass
                    print(f"[-] SSH Connection closed: {a}")
            
            # Handle each connection in a thread
            thread = threading.Thread(
                target=handle_connection,
                args=(client, addr),
                daemon=False
            )
            thread.start()
    
    except KeyboardInterrupt:
        print("\n[-] SSH Server shutdown")
    finally:
        sock.close()
