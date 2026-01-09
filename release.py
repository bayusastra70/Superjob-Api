import questionary
import subprocess
import sys
import re
from pathlib import Path

VERSION_FILE = Path("app/__init__.py")

def get_current_version():
    """Mencari string versi saat ini di file __init__.py"""
    if not VERSION_FILE.exists():
        print(f"❌ File {VERSION_FILE} tidak ditemukan!")
        sys.exit(1)
        
    content = VERSION_FILE.read_text()
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    
    if match:
        # Mengembalikan tuple (major, minor, patch) sebagai integer
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    else:
        print("❌ Tidak bisa menemukan format __version__ di app/__init__.py")
        sys.exit(1)

def release():
    major, minor, patch = get_current_version()
    current_ver_str = f"{major}.{minor}.{patch}"

    v_patch = f"{major}.{minor}.{patch + 1}"
    v_minor = f"{major}.{minor + 1}.0"
    v_major = f"{major + 1}.0.0"

    print(f"\nℹ️  Current version: \033[32m{current_ver_str}\033[0m\n")

    choice = questionary.select(
        "Select release type:",
        choices=[
            questionary.Choice(f"patch      {v_patch}", value="patch"),
            questionary.Choice(f"minor      {v_minor}", value="minor"),
            questionary.Choice(f"major      {v_major}", value="major"),
            questionary.Separator(),
            questionary.Choice(f"custom     ...", value="custom"),
            questionary.Choice(f"as-is      {current_ver_str}", value="as-is"),
            questionary.Separator(),
            questionary.Choice("❌ Cancel", value="cancel"),
        ],
        style=questionary.Style([
            ('qmark', 'fg:#5F819D bold'),      # Warna tanda tanya
            ('question', 'bold'),              # Warna pertanyaan
            ('answer', 'fg:#FF9D00 bold'),     # Warna jawaban yang dipilih
            ('pointer', 'fg:#FF9D00 bold'),    # Warna panah seleksi
            ('highlighted', 'fg:#FF9D00'),     # Warna pilihan yang disorot
        ])
    ).ask()

    if not choice or choice == "cancel":
        print("Release dibatalkan.")
        sys.exit()

    cmd = ["bumpver", "update"]

    if choice == "custom":
        # Kalau pilih custom, tanya mau versi berapa
        custom_ver = questionary.text("Enter version number:").ask()
        if not custom_ver:
            print("Versi tidak valid.")
            sys.exit()
        cmd.extend(["--set-version", custom_ver])
        display_ver = custom_ver
    
    elif choice == "as-is":
        print("Mode 'as-is' dipilih (Tidak ada perubahan versi).")
        sys.exit()
    
    else:
        # Patch/Minor/Major
        cmd.append(f"--{choice}")
        display_ver = {
            "patch": v_patch,
            "minor": v_minor,
            "major": v_major
        }[choice]

    print(f"\n🚀 Menyiapkan release: {display_ver}...")
    try:
        # Tambahkan --allow-dirty jika ingin membolehkan file yang belum dicommit
        # cmd.append("--allow-dirty") 
        subprocess.run(cmd, check=True)
        print("\n✅ Berhasil! Release selesai.")
    except subprocess.CalledProcessError:
        print("\n❌ Gagal menjalankan bumpver. Cek error di atas.")

if __name__ == "__main__":
    release()