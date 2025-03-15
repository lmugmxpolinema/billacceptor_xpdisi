import os
import re
import subprocess
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def print_log(message, level="info"):
    """Mencetak pesan ke terminal dan mencatat log."""
    if level == "info":
        print(f"✅ {message}")
        logging.info(message)
    elif level == "warning":
        print(f"⚠️ {message}")
        logging.warning(message)
    elif level == "error":
        print(f"❌ {message}")
        logging.error(message)

def run_command(command):
    """Menjalankan perintah shell dengan subprocess dan menangani error."""
    try:
        subprocess.run(command, check=True, shell=True)
        print_log(f"Berhasil menjalankan: {command}")
    except subprocess.CalledProcessError as e:
        print_log(f"Gagal menjalankan: {command}\nError: {e}", "error")

def install_dependencies():
    """Menginstal semua dependensi yang dibutuhkan."""
    print_log("📦 Menginstal dependensi...")
    dependencies = [
        "sudo apt update && sudo apt upgrade -y",
        "sudo apt install python3-pip -y",
        "sudo pip3 install flask requests --break-system-packages",
        "sudo pip3 install psutil flask_cors --break-system-packages",
        "sudo apt install -y ufw",
        "sudo systemctl start pigpiod",
        "sudo systemctl enable pigpiod"
    ]
    for dep in dependencies:
        run_command(dep)
    print_log("✅ Semua dependensi telah terinstal.")

def replace_line_in_file(filename, pattern, replacement):
    """Mengganti baris dalam file berdasarkan pola tertentu."""
    if not os.path.exists(filename):
        print_log(f"❌ File tidak ditemukan: {filename}", "error")
        return  
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
        
        with open(filename, "w") as file:
            for line in lines:
                if re.search(pattern, line):
                    file.write(replacement + "\n")
                else:
                    file.write(line)
        print_log(f"✅ Berhasil mengedit file: {filename}")
    except FileNotFoundError:
        print_log(f"❌ File tidak ditemukan: {filename}", "error")

def configure_files(python_path, log_dir, flask_port, device_id):
    """Mengedit file konfigurasi dengan parameter yang diberikan."""
    print_log("🛠️ Mengonfigurasi file...")
    replace_line_in_file("billacceptor.py", r'LOG_DIR = .*', f'LOG_DIR = "{log_dir}"')
    replace_line_in_file("billacceptor.py", r'ID_DEVICE = .*', f'ID_DEVICE = "{device_id}"')
    replace_line_in_file("billacceptor.py", r'app.run\(host="0.0.0.0", port=.*', f'app.run(host="0.0.0.0", port={flask_port}, debug=False, use_reloader=False)')
    replace_line_in_file("billacceptor.service", r'ExecStart=.*', f'ExecStart=/usr/bin/python3 {python_path}/billacceptor.py')

def move_files(python_path, rollback_path):
    """Memindahkan file ke lokasi yang sesuai."""
    print_log("📂 Memindahkan file konfigurasi...")
    run_command("sudo mv billacceptor.service /etc/systemd/system/")
    run_command(f"sudo mv billacceptor.py {python_path}")
    run_command(f"sudo mv rollback.py {rollback_path}")
    run_command(f"sudo mv setup.log {rollback_path}")

def configure_ufw(flask_port):
    """Mengonfigurasi firewall UFW."""
    print_log("🔐 Mengonfigurasi UFW...")
    run_command(f"sudo ufw allow {flask_port}")
    run_command("sudo ufw enable")

def enable_service():
    """Mengaktifkan service billacceptor."""
    print_log("🚀 Mengaktifkan service Bill Acceptor...")
    run_command("sudo systemctl enable billacceptor.service")
    run_command("sudo systemctl start billacceptor.service")

def write_setup_log(filename, data):
    """Menuliskan data setup ke dalam file log."""
    try:
        with open(filename, "a") as log_file:
            log_file.write(data + "\n")
    except PermissionError:
        print_log(f"❌ Tidak bisa menulis ke {filename}. Coba jalankan dengan sudo.", "error")
    except Exception as e:
        print_log(f"Gagal menulis log setup: {e}", "error")

def ensure_directory_exists(directory):
    """Membuat folder jika belum ada."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print_log(f"📁 Membuat folder: {directory}")
    else:
        print_log(f"✅ Folder sudah ada: {directory}")

if __name__ == "__main__":
    setup_log_file = "setup.log"
    print("\n🔧 **Setup Bill Acceptor**\n")

    # **Input dari pengguna**
    device_id = input("Masukkan ID Device: ")
    write_setup_log(setup_log_file, f"ID_DEVICE: {device_id}")

    python_path = input("Masukkan path penyimpanan billacceptor.py: ")
    ensure_directory_exists(python_path)
    write_setup_log(setup_log_file, f"Python Path: {python_path}")

    log_dir = python_path  
    print_log(f"📁 LOG_DIR disetel ke: {log_dir}")
    write_setup_log(setup_log_file, f"LOG_DIR: {log_dir}")

    flask_port = input("Masukkan port Flask: ")
    write_setup_log(setup_log_file, f"Flask Port: {flask_port}")

    rollback_path = input("Masukkan path penyimpanan rollback.py: ")
    ensure_directory_exists(rollback_path)
    write_setup_log(setup_log_file, f"Rollback Path: {rollback_path}")

    # **Jalankan semua fungsi**
    install_dependencies()
    configure_files(python_path, log_dir, flask_port, device_id)
    move_files(python_path, rollback_path)
    configure_ufw(flask_port)
    enable_service()

    print("\n🎉 **Setup selesai! Bill Acceptor sudah terinstal dan berjalan.** 🎉")
    print_log("🎉 Setup selesai! Bill Acceptor sudah terinstal dan berjalan.")
