#!/usr/bin/env python3
import paramiko
import sys

def test_ssh():
    """Test SSH connection to honeypot"""
    
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("[*] Connecting to SSH server...")
        
        # Connect
        client.connect(
            hostname='localhost',
            port=2222,
            username='testuser',
            password='testpass',
            allow_agent=False,
            look_for_keys=False,
            timeout=5
        )
        
        print("[+] SSH Connection successful!")
        
        # Open interactive shell
        transport = client.get_transport()
        channel = transport.open_session()
        channel.invoke_shell()
        
        # Send commands
        commands = ['ls\n', 'pwd\n', 'exit\n']
        
        for cmd in commands:
            print(f"[>] Sending: {cmd.strip()}")
            channel.send(cmd)
            
            # Read output
            import time
            time.sleep(0.5)
            if channel.recv_ready():
                output = channel.recv(1024).decode('utf-8', errors='ignore')
                print(output)
        
        channel.close()
        client.close()
        
        print("[+] Test completed successfully!")
        return True
    
    except Exception as e:
        print(f"[-] SSH Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ssh()
    sys.exit(0 if success else 1)
