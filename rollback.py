import os
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

def read_setup_log(log_path):
    """Membaca setup.log untuk mendapatkan informasi konfigurasi."""
    config = {}
    if not os.path.exists(log_path):
        print_log("setup.log tidak ditemukan, rollback dibatalkan.", "error")
        exit()
    
    with open(log_path, "r") as file:
        for line in file:
            if "Python Path:" in line:
                config["python_path"] = line.split(":")[1].strip()
            elif "LOG_DIR:" in line:
                config["log_dir"] = line.split(":")[1].strip()
            elif "Flask Port:" in line:
                config["flask_port"] = line.split(":")[1].strip()
            elif "VPN Log Path:" in line:
                config["vpn_log"] = line.split(":")[1].strip()
    return config

def uninstall_dependencies():
    """Menghapus semua dependensi yang telah diinstal."""
    print_log("📦 Menghapus dependensi yang telah diinstal...")
    dependencies = [
        "sudo apt autoremove -y",
        "sudo pip3 uninstall -y flask requests psutil flask_cors",
        "sudo apt remove --purge -y python3-pip pptp-linux ufw",
    ]
    for dep in dependencies:
        run_command(dep)
    print_log("✅ Semua dependensi telah dihapus.")
def remove_files(python_path, log_dir, vpn_log):
    """Menghapus file konfigurasi, logs, dan service."""
    print_log("🗑️ Menghapus file konfigurasi dan logs...")

    files_to_remove = [
        f"{python_path}/billacceptor.py",
        "/etc/systemd/system/billacceptor.service",
        "/etc/ppp/peers/vpn",
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            run_command(f"sudo rm -f {file}")
        else:
            print_log(f"File {file} tidak ditemukan, mungkin sudah dihapus.", "warning")

    # Hapus direktori log jika ada
    if os.path.exists(log_dir):
        run_command(f"sudo rm -rf {log_dir}")

    # Hapus VPN log jika ada
    if vpn_log and os.path.exists(vpn_log):
        run_command(f"sudo rm -rf {vpn_log}")

def disable_service():
    """Menonaktifkan dan menghapus service billacceptor."""
    print_log("🚫 Menonaktifkan dan menghapus service Bill Acceptor...")
    run_command("sudo systemctl stop billacceptor.service")
    run_command("sudo systemctl disable billacceptor.service")
    run_command("sudo rm -f /etc/systemd/system/billacceptor.service")
    run_command("sudo systemctl daemon-reload")

def reset_firewall(flask_port):
    """Menghapus aturan firewall UFW yang telah ditambahkan."""
    print_log("🔐 Menghapus aturan firewall UFW...")
    run_command(f"sudo ufw deny {flask_port}")
    run_command("sudo ufw disable")

def clear_crontab():
    """Mengosongkan crontab pengguna."""
    print_log("🗑️ Mengosongkan crontab...")
    run_command("crontab -r")

def clear_rc_local():
    """Menghapus baris 'vpn=\"on\"' dari /etc/rc.local tanpa mengubah bagian lain."""
    rc_local_path = "/etc/rc.local"

    if os.path.exists(rc_local_path):
        with open(rc_local_path, "r") as file:
            lines = file.readlines()

        # Hapus baris yang mengandung `vpn="on"`
        new_lines = [line for line in lines if 'vpn="on"' not in line]

        # Tulis ulang isi file tanpa baris tersebut
        with open(rc_local_path, "w") as file:
            file.writelines(new_lines)

        print("✅ Berhasil menghapus 'vpn=\"on\"' dari /etc/rc.local")
    else:
        print("❌ File /etc/rc.local tidak ditemukan!")

def clone_repository():
    """Menanyakan apakah ingin clone repository dan direktori tujuan jika ya."""
    choice = input("🔄 Apakah Anda ingin meng-clone ulang repository Bill Acceptor? (y/n): ").strip().lower()
    if choice == "y":
        clone_dir = input("Masukkan direktori tujuan untuk clone repository: ").strip()
        if os.path.exists(clone_dir):
            print_log(f"🗑️ Menghapus isi direktori {clone_dir}...")
            run_command(f"sudo rm -rf {clone_dir}/*")
        else:
            print_log(f"📂 Direktori {clone_dir} tidak ditemukan, membuatnya terlebih dahulu...")
            os.makedirs(clone_dir)
        print_log("🔄 Meng-clone repository...")
        run_command(f"git clone https://github.com/GTT008/billacceptor_beta {clone_dir}")

if __name__ == "__main__":
    print("\n🔧 **Rollback Bill Acceptor**\n")
    
    # Membaca konfigurasi dari setup.log
    setup_log_path = "setup.log"
    config = read_setup_log(setup_log_path)
    
    # Menjalankan rollback otomatis
    remove_files(config["python_path"], config["log_dir"], config["vpn_log"])  # ✅ FIX KeyError
    disable_service()
    reset_firewall(config["flask_port"])  # ✅ FIX KeyError
    clear_crontab()
    clear_rc_local()
    uninstall_dependencies()
    # Clone repository jika diinginkan
    clone_repository()
    
    print("\n🎉 **Rollback selesai! Semua konfigurasi telah dihapus.** 🎉")