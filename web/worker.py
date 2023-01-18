import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests

from celery import Celery
from dotenv import load_dotenv

from app.models import User
from app.logger import logger

BACKUP_MAX_COUNT = 10
BACKUP_PERIOD = 60 * 60 * 24
BACKUP_DIR = os.environ.get("BACKUP_DIR")

load_dotenv()

REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_ADDR = os.environ.get("REDIS_ADDR", f"localhost:{REDIS_PORT}")
BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_ADDR}"

app = Celery('tasks', broker=BROKER_URL)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(BACKUP_PERIOD, do_backup.s())


@app.task
def check_and_alert():
    url = f"http://localhost:5000/api_email_alert"
    users: list[User] = User.query.all()
    off_30_min_users = 0
    no_update_files_2h = 0

    for user in users:
        if user.last_download_time < datetime.now() - timedelta.seconds(43200):
            # TODO put support email here to send and receive emails
            requests.post(url, json={
                "from_email":"sup_send@eamil.com",
                "to_addresses":"sup_receive@eamil.com",
                "subject":f"User {user.username} 12 hours alert!",
                "body":f"User {user.username} from client {user.client} had not download files for more then 12 hours."})
            logger.info("User {user.username} 12 hours alert sent.")
        
        if user.last_time_online < datetime.now() - timedelta.seconds(43200):
            # TODO put support email here to send and receive emails
            requests.post(url, json={
                "from_email":"sup_send@eamil.com",
                "to_addresses":"sup_receive@eamil.com",
                "subject":f"User {user.username} 12 hours offline alert!",
                "body":f"User {user.username} from client {user.client} had not been online for more then 12 hours."})
            logger.info("User {user.username} 12 hours offline alert sent.")
        
        if user.last_time_online < datetime.now() - timedelta.seconds(1800):
            off_30_min_users +=1
        
        if user.last_download_time < datetime.now() - timedelta.seconds(7200):
            no_update_files_2h +=1

    if off_30_min_users == len(users):
        # TODO put support email here to send and receive emails
        requests.post(url, json={
            "from_email":"sup_send@eamil.com",
            "to_addresses":"sup_receive@eamil.com",
            "subject":f"All users offline 30 min alert!",
            "body":f"All users are offline more then 30 minutes."})
        logger.info("All users offline 30 min alert sent.")
    
    if no_update_files_2h == len(users):
        # TODO put support email here to send and receive emails
        requests.post(url, json={
            "from_email":"sup_send@eamil.com",
            "to_addresses":"sup_receive@eamil.com",
            "subject":f"No new files over 2 h alert!",
            "body":f"No new files were downloaded by all users for over 2 hours."})
        logger.info("No new files over 2 h alert sent.")



@app.task
def do_backup():
    all_backups = [f for f in os.listdir(BACKUP_DIR) if (Path(BACKUP_DIR) / f).is_file()]
    all_timestamps = []

    for backup in all_backups:
        backup_timestamp = backup.split(BACKUP_FILENAME_POSTFIX)[0]
        try:
            backup_timestamp = float(backup_timestamp)
            all_timestamps.append(backup_timestamp)
        except ValueError:
            continue

    make_backup(time.time())
    all_timestamps.sort()
    timestamps_to_delete_count = len(all_timestamps) - BACKUP_MAX_COUNT + 1
    timestamps_to_delete_count = 0 if timestamps_to_delete_count < 0 else timestamps_to_delete_count
    for i in range(timestamps_to_delete_count):
        os.remove(f"{BACKUP_DIR}/{all_timestamps[i]}{BACKUP_FILENAME_POSTFIX}")