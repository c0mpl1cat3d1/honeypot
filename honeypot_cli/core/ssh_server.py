import paramiko
import os
import threading
import socket
import datetime
from paramiko import ServerInterface
from core.cli import load_command


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
    
    def run_command(self, command):
        """Execute a command"""
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
            return None  # Signal to close
        
        if cmd == "pwd":
            return self.current_directory
        
        # External commands
        module = load_command(cmd)
        if module:
            try:
                output = module.run(args, self.current_directory)
                return output if output else ""
            except Exception as e:
                return f"Error: {str(e)}"
        else:
            return f"{cmd}: command not found"
    
    def handle_shell(self):
        """Handle interactive shell"""
        try:
            # Send banner
            self.channel.send(b"Welcome to Ubuntu 20.04 LTS\n")
            self.channel.send(b"login successful\n\n")
            
            while True:
                # Send prompt
                prompt = self.get_prompt()
                self.channel.send(prompt.encode())
                
                # Receive command
                try:
                    data = self.channel.recv(1024)
                    if not data:
                        break
                except:
                    break
                
                command = data.decode('utf-8', errors='ignore').strip()
                if not command:
                    continue
                
                # Log
                self.log_command(command)
                
                # Execute
                result = self.run_command(command)
                if result is None:
                    self.channel.send(b"logout\n")
                    break
                
                if result:
                    self.channel.send((result + "\n").encode())
        
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
    
    def check_channel_shell_request(self, channel):
        """Accept shell channel requests"""
        # Create handler and run in thread
        handler = SSHShellHandler(channel, self.username or "guest")
        thread = threading.Thread(target=handler.handle_shell, daemon=False)
        thread.start()
        return paramiko.OPEN_SUCCEEDED


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
                    
                    # Keep the transport alive by waiting on it
                    # Don't call accept() - let paramiko handle channels automatically
                    import time
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


