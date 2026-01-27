import os
import shutil
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
MEDIA_PATH = os.path.join(BASE_DIR, "media")\

print("BASE_DIR =", BASE_DIR)
print("DB EXISTS =", os.path.exists(DB_PATH))
print("MEDIA_EXISTS =", os.path.exists(MEDIA_PATH))




BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_BACKUP_DIR = os.path.join(BACKUP_DIR, "db")
MEDIA_BACKUP_DIR = os.path.join(BACKUP_DIR, "media")

KEEP_DAYS = 7

os.makedirs(DB_BACKUP_DIR, exist_ok=True)
os.makedirs(MEDIA_BACKUP_DIR, exist_ok=True)

now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

db_backup_file = os.path.join(DB_BACKUP_DIR, f"db_{now}.sqlite3")
shutil.copy2(DB_PATH, db_backup_file)

media_backup_folder = os.path.join(MEDIA_BACKUP_DIR, f"media_{now}")
if os.path.exists(MEDIA_PATH):
    shutil.copytree(MEDIA_PATH, media_backup_folder)

print(" Backup created:")
print("DB  ->", db_backup_file)
print("Media->", media_backup_folder)

def cleanup_old_backups(folder, days):
    cutoff = datetime.now() - timedelta(days=days)

    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        try:
            time_str = name.split("_", 1)[1]
            time_str = time_str.replace(".sqlite3", "")
            backup_time = datetime.strptime(time_str, "%Y-%m-%d_%H-%M-%S")
        except:
            continue

        if backup_time < cutoff:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            print(" Deleted old backup:", path)

cleanup_old_backups(DB_BACKUP_DIR, KEEP_DAYS)
cleanup_old_backups(MEDIA_BACKUP_DIR, KEEP_DAYS)

print("cleanup done.")
            
                        
