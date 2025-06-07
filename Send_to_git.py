import os
import io
import subprocess
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# === CONFIG ===
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/drive']

# PAS DIT PAD AAN NAAR JOUW ECHTE GIT-REPO MAP
LOCAL_REPO = os.path.expanduser("~/EUV_TEST/euv-pipeline/repo_5_resultaat")

FOLDER_MAP = {
    '1Nh2_-lsQpUDY3E5vuQqgGsHV7Vgbj8AT': 'reduced_votes',
    '1cDNDyPKhSDelf2YuL-2jtjgvTXoPO0W6': 'resultaat',
    '1Jt3o0S9crNExpYCy3H5O_d1w8AXgMcFf': 'ranking_per_land'
}

# === Setup Google Drive API ===
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# === Functie: Download van Drive naar lokale map ===
def download_drive_files():
    print("🔽 Bestanden downloaden uit Google Drive...")
    for folder_id, subdir in FOLDER_MAP.items():
        local_path = os.path.join(LOCAL_REPO, subdir)
        os.makedirs(local_path, exist_ok=True)

        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        for file in files:
            filename = file['name']
            file_id = file['id']
            dest_path = os.path.join(local_path, filename)
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.FileIO(dest_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            print(f"✅ Gedownload: {filename} → {subdir}/")

# === Check of LOCAL_REPO een git repo is ===
def is_git_repo(path):
    git_dir = os.path.join(path, '.git')
    return os.path.isdir(git_dir)

# === Functie: Git commit + push ===
def git_push():
    if not is_git_repo(LOCAL_REPO):
        print(f"❌ FOUT: '{LOCAL_REPO}' is géén git repository. Controleer je LOCAL_REPO pad!")
        return

    commit_msg = f"🔄 Update uit Google Drive - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print("📤 Bestand naar GitHub pushen...")

    cmds = [
        "git add .",
        f"git commit -m \"{commit_msg}\"",
        "git push origin main"  # Pas eventueel 'main' aan
    ]

    for cmd in cmds:
        result = subprocess.run(cmd, cwd=LOCAL_REPO, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            if "nothing to commit" in result.stderr:
                print("ℹ️ Geen wijzigingen om te committen.")
                return
            else:
                print(f"❌ Git-fout: {cmd}")
                print(result.stderr)
        else:
            print(f"✅ Git-opdracht uitgevoerd: {cmd}")

# === Main flow ===
if __name__ == "__main__":
    download_drive_files()
    git_push()
