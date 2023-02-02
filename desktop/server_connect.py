import os
from subprocess import Popen, PIPE
import stat
import time
import datetime
import json
import getpass
from pathlib import Path
import tempfile

import requests
from paramiko import SSHClient, AutoAddPolicy, AutoAddPolicy
from loguru import logger

import pprint

storage_path = os.path.join(os.environ.get("APPDATA"), Path("EmarDir"))

log_format = "{time} - {name} - {level} - {message}"
logger.add(
    sink=os.path.join(storage_path, "emar_log.txt"),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)
        return False
    return True


if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Error: {e}")
        raise Exception("Can't find manager_host in config.json. Check that field and file exist.")
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")


creds_file = "creds.json"
# local_creds_json = f"{os.getcwd()}\{creds_file}"
local_creds_json = os.path.join(storage_path, creds_file)
logger.info(f"local_creds_json var is {local_creds_json}")


# create .ssh folder if doesn't exist with known_hosts inside
ssh_exists = mknewdir(os.path.join(Path().home(), ".ssh"))
if not ssh_exists:
    open(os.path.join(Path().home(), Path(".ssh/known_hosts")), 'a').close()


def register_computer():
    import socket
    import platform

    computer_name = socket.gethostname()
    logger.debug("Computer Name {}, type {}", computer_name, type(computer_name))
    if not isinstance(computer_name, str):
        computer_name = platform.node()
        logger.debug("Computer Name {}, type {}", computer_name, type(computer_name))
    if not isinstance(computer_name, str):
        raise(ValueError("Can't get computer name. Name {}, type {}", computer_name, type(computer_name)))
    identifier_key = "new_computer"

    response = requests.post(f"{g_manager_host}/register_computer", json={
        "computer_name": computer_name,
        "identifier_key": identifier_key,
    })

    logger.debug("response.request.method on /register_computer {}", response.request.method)

    if response.request.method == "GET":
        logger.warning("Instead of POST method we have GET on /register_computer. Retry with allow_redirects=False")
        response = requests.post(f"{g_manager_host}/register_computer", allow_redirects=False,  json={
            "computer_name": computer_name,
            "identifier_key": identifier_key,
        })
        print("response.history", response.history)
        logger.debug("Retry response.request.method on /register_computer. Method = {}", response.request.method)

    if response.status_code == 200:
        logger.info("New computer registered. Download will start next time if credentials inserted to DB.")
    else:
        logger.warning("Something went wrong. Response status code = {}", response.status_code)

    print("else response.json()", response.json())
    return response


@logger.catch
def get_credentials():
    logger.info("Recieving credentials.")
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")

        computer_name = creds_json["computer_name"]
        identifier_key = creds_json["identifier_key"]
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host

        response = requests.post(f"{manager_host}/get_credentials", json={
            "computer_name": computer_name,
            "identifier_key": str(identifier_key),
        })
        # print("if response.json()", response.json())

        if "rmcreds" in response.json():
            if os.path.isfile(local_creds_json):
                os.remove(local_creds_json)
                logger.warning("Remote server can't find computer {}. Deleting creds.json and registering current computer.", computer_name)
                register_computer()

    else:
        response = register_computer()
        
    if response.json()["message"] == "Supplying credentials" or response.json()["message"] == "Computer registered":
        with open(local_creds_json, "w") as f:
            json.dump(
                {
                    "computer_name": response.json()["computer_name"],
                    "identifier_key": response.json()["identifier_key"],
                    "manager_host": response.json()["manager_host"]
                },
                f
            )
            logger.info(f"Full credentials recieved from server and {local_creds_json} updated.")

        return response.json()
    
    else:
        raise ValueError("Wrong response data. Can't proceed without correct credentials.")


@logger.catch
def sftp_check_files_for_update_and_load(credentials):

    # key = path, value = checksum
    files_cheksum = {}
    print('credentials["files_checksum"]', type(credentials["files_checksum"]))
    pprint.pprint(credentials["files_checksum"])
    download_directory = credentials["sftp_folder_path"] if credentials["sftp_folder_path"] else "."

    with SSHClient() as ssh:
        # TODO check for real key
        ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        try:
            ssh.connect(
                credentials["host"],
                username=credentials["sftp_username"],
                password=credentials["sftp_password"],
                timeout=10,
                auth_timeout=10
            )
        except Exception as e:
            raise Exception(e)

        with ssh.open_sftp() as sftp:
            # get list of all files and folders on sftp server
            findin, findout, finderr = ssh.exec_command(f"find .")
            str_content_paths: str = findout.read().decode()
            if str_content_paths:
                list_content_paths: list = str_content_paths.split("\r\n")
                print("\nlist_content_paths:")
                pprint.pprint(list_content_paths)
                # get checksum of all aplicable files
                for content in list_content_paths:
                    print("content", content)
                    content_to_checksum = content if download_directory in content else None
                    print("content_to_checksum", content_to_checksum)
                    if content_to_checksum:
                        shain, shaout, shaerr = ssh.exec_command(f'sha256sum {content}')
                        str_err = shaerr.read().decode()
                        str_sha: str = shaout.read().decode() if not str_err else ""
                        print("str_sha", str_sha)
                        print("str_err", str_err)

                        if str_sha:
                            files_cheksum[content] = str_sha.split()[0]

                print(f"\nfiles_cheksum: {type(files_cheksum)}")
                pprint.pprint(files_cheksum)

            else:
                str_error: str = finderr.read().decode()
                print(f"\nstr_error: {str_error}\n")

            update_download_status("downloading", credentials)
            prefix=f"backup_{time.ctime()}_".replace(":", "-").replace(" ", "_")
            suffix=f"_timestamp{datetime.datetime.now().timestamp()}"

            with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix) as tempdir:
                files_loaded = 0
                for filepath in files_cheksum:
                    # chdir to be on top dir level
                    sftp.chdir(None)
                    # if download_directory != ".":
                    #     sftp.chdir(download_directory)
                    print(f"filepath: {filepath}")
                    dirpath: list = filepath.split("/")[1:-1]
                    print(f"dirpath: {dirpath}")
                    filename: str = filepath.split("/")[-1]
                    print(f"filename: {filename}")
                    dirname = "/".join(dirpath)
                    print(f"checking: {dirname}/{filename}")

                    # get and create local temp directory if not exists
                    local_temp_emar_dir = os.path.join(tempdir, Path(dirname)) if dirname else tempdir
                    if not os.path.exists(local_temp_emar_dir):
                        os.mkdir(local_temp_emar_dir)
                    print("local_temp_emar_dir", local_temp_emar_dir)

                    # get file from sftp server if it was changed
                    # TODO what if file in the root
                    print("files_cheksum[filepath]", files_cheksum[filepath])
                    if filepath not in credentials["files_checksum"]:
                        sftp.chdir(dirname)
                        sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                        print(f"downloaded: {dirname}/{filename}\n")
                        files_loaded += 1
                    elif files_cheksum[filepath] not in credentials["files_checksum"][filepath]:
                        print('credentials["files_checksum"][filepath]', credentials["files_checksum"][filepath])
                        sftp.chdir(dirname)
                        sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                        print(f"downloaded: {dirname}/{filename}\n")
                        files_loaded += 1
                    else:
                        print(f"NOT downloaded: {dirname}/{filename} file is not changed\n")

                sftp.close()
                
                if files_loaded > 0:
                    zip_name = os.path.join(storage_path, "emar_backups.zip")
                    print("zip_name", zip_name)
                    subprs = Popen([
                            Path(".") / "7z.exe",
                            "a",
                            zip_name,
                            tempdir,
                            f'-p{credentials["folder_password"]}'
                        ])
                    subprs.communicate()

                    logger.info("Files zipped.")

                    proc = Popen([Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name], stdout=PIPE)
                    files = [l.split('Path = ')[1] for l in proc.stdout.read().decode().splitlines() if l.startswith('Path = ')]
                    dirs = [i for i in files if "\\" not in i]
                    dirs.sort(key = lambda x: x.split("timestamp")[1])
                    pprint.pprint(f"dirs:\n{dirs}")

                    # TODO should we make this configurable?
                    if len(dirs) > 12:
                        diff = len(dirs) - 12
                        for dir_index in range(diff):
                            subprs = Popen([
                                    Path(".") / "7z.exe",
                                    "d",
                                    zip_name,
                                    dirs[dir_index],
                                    "-r",
                                    f'-p{credentials["folder_password"]}'
                                ])
                            subprs.communicate()

                    proc = Popen([Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name], stdout=PIPE)
                    files = [l.split('Path = ')[1] for l in proc.stdout.read().decode().splitlines() if l.startswith('Path = ')]
                    ddirs = [i for i in files if "\\" not in i]
                    ddirs.sort(key = lambda x: x.split("timestamp")[1])
                    pprint.pprint(f"after delete dirs:\n{ddirs}")
                    
                else:
                    logger.info("Nothing to zip.")

                update_download_status("downloaded", credentials, last_downloaded=str(tempdir))

        response = requests.post(f"{credentials['manager_host']}/files_checksum", json={
                    "files_checksum": files_cheksum,
                    "identifier_key": str(credentials['identifier_key']),
                    "last_time_online": str(datetime.datetime.now())
                })
        logger.debug("files_cheksum sent to server. Response status code = {}", response.status_code)

    return datetime.datetime.now()


@logger.catch
def send_activity(last_download_time, creds):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
    else:
        manager_host = g_manager_host

    url = f"{manager_host}/last_time"
    requests.post(url, json={
    "company_name": creds["company_name"],
    "identifier_key": creds["identifier_key"],
    "location_name": creds["location_name"],
    "last_download_time": str(last_download_time),
    "last_time_online": str(datetime.datetime.now())
    })
    logger.info("User last time download sent.")


@logger.catch
def update_download_status(status, creds, last_downloaded=""):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
    else:
        manager_host = g_manager_host

    url = f"{manager_host}/download_status"
    requests.post(url, json={
    "company_name": creds["company_name"],
    "location_name": creds["location_name"],
    "download_status": status,
    "last_time_online": str(datetime.datetime.now()),
    "identifier_key": creds["identifier_key"],
    "last_downloaded": last_downloaded
    })
    logger.info(f"Download status: {status}.")


@logger.catch
def main_func():
    logger.info("Downloading proccess started.")
    credentials = get_credentials() 
    print("\ncredentials", credentials, "\n")
    if not credentials:
        raise ValueError("Credentials not supplayed. Can't continue.")

    if credentials["status"] == "success":
        last_download_time = sftp_check_files_for_update_and_load(credentials)
        # last_download_time = datetime.datetime.now()  # TODO for testing purpose, remove in prod
        send_activity(last_download_time, credentials)
        logger.info("Downloading proccess finished.")

        user = getpass.getuser()

        path = fr"C:\\Users\\{user}\\Desktop\\EMAR.lnk"  #This is where the shortcut will be created

        if not os.path.exists(path):

            from win32com.client import Dispatch

            target = fr"{os.path.join(storage_path, 'emar_backups.zip')}" # directory to which the shortcut is created
            wDir = fr"{storage_path}"

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.WorkingDirectory = wDir
            shortcut.Targetpath = target
            shortcut.save()
    
    elif credentials["status"] == "registered":
        logger.info("New computer registered. Download will start next time if credentials available in DB.")

    else:
        logger.info(f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}")
        time.sleep(60)

try:
    main_func()
    print("Task finished")
    time.sleep(60)
except Exception as e:
    print(f"Exception occured: {e}")
    time.sleep(120)

