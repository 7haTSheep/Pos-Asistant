import paramiko
import os
import sys

HOSTNAME = "192.168.1.159"
USERNAME = "denton"
PASSWORD = "io$jf82k"
LOCAL_DIR = r"c:\Users\GibboTech\Downloads\Pos-Asistant"
REMOTE_DIR = "/home/denton/Pos-Asistant"

def ensure_remote_dir(sftp, remote_path):
    try:
        sftp.stat(remote_path)
    except IOError:
        parent = os.path.dirname(remote_path).replace("\\", "/")
        if parent and parent != '/' and parent != remote_path:
            ensure_remote_dir(sftp, parent)
        try:
            sftp.mkdir(remote_path)
        except IOError:
            pass

def sync_directory(ssh, sftp, local_dir, remote_dir):
    for root, dirs, files in os.walk(local_dir):
        # Exclude common large/unnecessary dirs
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.venv', '__pycache__', 'build', 'dist', '.idea', '.vscode', 'deploy_to_server.py']]
        
        rel_path = os.path.relpath(root, local_dir)
        rel_path = rel_path.replace("\\", "/") # For remote unix path
        
        target_dir = remote_dir if rel_path == '.' else f"{remote_dir}/{rel_path}"
        ensure_remote_dir(sftp, target_dir)
        
        for file in files:
            local_file = os.path.join(root, file)
            remote_file = f"{target_dir}/{file}"
            print(f"Uploading {local_file} to {remote_file}")
            sftp.put(local_file, remote_file)


def main():
    print("Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    sftp = ssh.open_sftp()
    
    print(f"Creating remote workspace at {REMOTE_DIR}...")
    ssh.exec_command(f'mkdir -p {REMOTE_DIR}')
    
    print("Transferring files...")
    sync_directory(ssh, sftp, LOCAL_DIR, REMOTE_DIR)
    print("Transfer complete.")
    
    # Check dependencies and install if needed
    print("Checking dependencies on server...")
    
    commands = [
        "sudo -S apt update",
        "sudo -S apt install -y python3 python3-pip python3-venv nodejs npm",
        f"cd {REMOTE_DIR}/server && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt",
        f"cd {REMOTE_DIR}/client && npm install"
    ]
    
    for cmd in commands:
        print(f"Running command: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        if "sudo" in cmd:
            stdin.write(PASSWORD + "\n")
            stdin.flush()
        
        exit_status = stdout.channel.recv_exit_status()
        print(f"Exit status: {exit_status}")
        # Only print first 500 chars of output to avoid terminal spam
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        print("Output:", out[:500] + ("..." if len(out) > 500 else ""))
        if err:
            print("Error:", err[:500] + ("..." if len(err) > 500 else ""))
        
    sftp.close()
    ssh.close()
    print("Deployment script finished successfully.")

if __name__ == '__main__':
    main()
