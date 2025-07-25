"""SMB Connection Manager."""

import csv
import fnmatch
import os
import pickle
import tempfile
from io import TextIOWrapper
from pathlib import Path
from typing import IO, Any, Dict, Generator, List, Optional

from flask import current_app as app
from pathvalidate import sanitize_filename
from smbclient import makedirs, open_file, register_session, walk
from smbclient.path import exists, getsize
from smbclient.shutil import copyfile
from smbprotocol.exceptions import LogonFailure, SMBException
from smbprotocol.session import Session

from runner import redis_client
from runner.model import ConnectionSmb, Task
from runner.scripts.em_file import file_size
from runner.scripts.em_messages import RunnerException, RunnerLog
from scripts.crypto import em_decrypt


def connection_json(connection: Session) -> Dict:
    """Convert the connection string to json."""
    return {
        "server_name": connection.connection.server_name,
        "password": em_decrypt(connection.password, app.config["PASS_KEY"]),
        "username": str(connection.username),
    }


def connect(username: str, password: str, server_name: str) -> Session:
    """Connect to SMB server.

    After making a connection we save it to redis. Next time we need a connection
    we can grab if from redis and attempt to use. If it is no longer connected
    then reconnect.

    Because we want to use existing connection we will not close them...
    """
    redis_key = f"smb_session_{server_name}"

    def build_connect() -> Session:
        try:
            conn = register_session(
                server=server_name,
                username=username,
                password=em_decrypt(password, app.config["PASS_KEY"]),
            )

            redis_client.set(
                redis_key,
                pickle.dumps(
                    {"server_name": server_name, "username": username, "password": password}
                ),
            )

            return conn
        except LogonFailure as err:
            raise ValueError(f"Authentication failed: {err}")
        except SMBException as err:
            raise ValueError(f"SMB registration failed: {err}")
        except Exception as err:
            raise ValueError(f"Unexpected error during registration: {err}")

    session_data = redis_client.get(redis_key)
    if session_data:
        try:
            session_info = pickle.loads(session_data)
            conn = register_session(
                server=session_info["server_name"],
                username=session_info["username"],
                password=session_info["password"],
            )
        except Exception:
            conn = build_connect()
    else:
        conn = build_connect()

    return conn


class Smb:
    """SMB Connection Handler Class.

    smb.read = returns contents of a network file
    smb.save = save contents of local file to network file
    """

    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        connection: Optional[ConnectionSmb],
        directory: Path,
    ):
        """Set up class parameters."""
        # pylint: disable=too-many-arguments
        self.task = task
        self.run_id = run_id
        self.connection = connection
        self.dir = directory

        if self.connection is not None:
            self.share_name = str(self.connection.share_name).strip("/").strip("\\")
            self.username = self.connection.username
            self.password = self.connection.password
            self.server_name = self.connection.server_name if self.connection else "Error"
        else:
            # default connection for backups
            self.share_name = app.config["SMB_DEFAULT_SHARE"].strip("/").strip("\\")
            self.username = app.config["SMB_USERNAME"]
            self.password = app.config["SMB_PASSWORD"]
            self.server_name = app.config["SMB_SERVER_NAME"]
            self.subfolder = app.config.get("SMB_SUBFOLDER")

        self.conn = self.__connect()

    def __connect(self) -> Session:
        """Connect to SMB server.

        After making a connection we save it to redis. Next time we need a connection
        we can grab if from redis and attempt to use. If it is no longer connected
        then reconnect.

        Because we want to use existing connection we will not close them...
        """
        try:
            return connect(
                str(self.username),
                str(self.password),
                str(self.server_name),
            )
        except ValueError as e:
            raise RunnerException(self.task, self.run_id, 10, str(e))

    def __load_file(self, file_name: str, index: int, length: int) -> IO[Any]:

        original_name = Path(file_name).name
        RunnerLog(self.task, self.run_id, 10, f"({index} of {length}) downloading {original_name}")

        open_file_for_read = open_file(file_name, "rb")

        def load_data(file_obj: TextIOWrapper) -> Generator:
            with file_obj as this_file:
                while True:
                    data = this_file.read(1024)
                    if not data:
                        break
                    yield data

        # send back contents

        with tempfile.NamedTemporaryFile(mode="wb+", delete=False, dir=self.dir) as data_file:
            for data in load_data(open_file_for_read):
                if self.task.source_smb_ignore_delimiter != 1 and self.task.source_smb_delimiter:
                    my_delimiter = self.task.source_smb_delimiter or ","

                    csv_reader = csv.reader(
                        data.splitlines(),
                        delimiter=my_delimiter,
                    )
                    writer = csv.writer(data_file)
                    writer.writerows(csv_reader)

                else:
                    data_file.write(data)

            if os.path.islink(original_name):
                os.unlink(original_name)
            elif os.path.isfile(original_name):
                os.remove(original_name)
            os.link(data_file.name, original_name)
            data_file.name = original_name  # type: ignore[misc]

        open_file_for_read.close()

        return data_file

    def read(self, file_name: str) -> List[IO[str]]:
        """Read file contents of network file path.

        Data is loaded into a temp file.

        Returns a path or raises an exception.
        """
        try:
            # if there is a wildcard in the filename
            if "*" in file_name:
                RunnerLog(self.task, self.run_id, 10, "Searching for matching files...")

                # a smb file name can be a path, but listpath
                # will only list current folder.
                # we need to split the filename path and iter
                # through the folders that match.

                # get the path up to the *.
                base_dir = str(Path(file_name.split("*")[0]).parent)

                file_list = []
                for path, _, walk_file_list in walk(base_dir):
                    for this_file in walk_file_list:
                        if fnmatch.fnmatch(this_file, file_name):
                            file_list.append(str(Path(path).joinpath(this_file)))

                RunnerLog(
                    self.task,
                    self.run_id,
                    10,
                    "Found %d file%s.\n%s"
                    % (
                        len(file_list),
                        ("s" if len(file_list) != 1 else ""),
                        "\n".join(file_list),
                    ),
                )

                # if a file was found, try to open.
                return [
                    self.__load_file(file_name, i, len(file_list))
                    for i, file_name in enumerate(file_list, 1)
                ]

            return [self.__load_file(file_name, 1, 1)]
        except BaseException as e:
            raise RunnerException(
                self.task,
                self.run_id,
                10,
                f"File failed to load file from server.\n{e}",
            )

    # pylint: disable=R1710
    def save(self, overwrite: int, file_name: str) -> str:  # type: ignore[return]
        """Load data into network file path, creating location if not existing."""
        try:
            if self.connection is not None:
                dest_path = str(
                    Path(self.connection.server_name or "")
                    / Path(self.connection.share_name or "")
                    / Path(self.connection.path or "").joinpath(file_name)
                )
            else:
                dest_path = str(
                    Path(
                        Path(sanitize_filename(self.server_name or ""))
                        / Path(sanitize_filename(self.share_name or ""))
                        / (
                            Path(
                                Path(sanitize_filename(self.subfolder or ""))
                                / Path(sanitize_filename(self.task.project.name or ""))
                            )
                            if self.subfolder
                            else Path(sanitize_filename(self.task.project.name or ""))
                        )
                        / sanitize_filename(self.task.name or "")
                        / sanitize_filename(self.task.last_run_job_id or "")
                        / file_name
                    )
                )

            smb_path = f"\\\\{dest_path}"

            my_dir = str(Path(smb_path).parent)

            # makedirs will create the folders. If parent doesn't exist, it will create that also.
            try:
                makedirs(my_dir, exist_ok=True)
            except (OSError, SMBException) as e:
                raise RunnerException(
                    self.task, self.run_id, 10, f"Failed to create SMB directory: {my_dir}\n{e}"
                )

            if overwrite != 1 and exists(smb_path):
                RunnerLog(
                    self.task,
                    self.run_id,
                    10,
                    "File already exists and will not be loaded",
                )
                return smb_path

            try:
                copyfile(self.dir.joinpath(file_name), smb_path)
            except FileNotFoundError as e:
                raise RunnerException(self.task, self.run_id, 10, f"Source file not found: {e}")
            except PermissionError as e:
                raise RunnerException(
                    self.task, self.run_id, 10, f"Permission denied while copying file: {e}"
                )
            except Exception as e:
                raise RunnerException(
                    self.task, self.run_id, 10, f"Unexpected error during file copy: {e}"
                )
            uploaded_size = getsize(smb_path)

            server_name = "backup" if self.connection is None else self.connection.server_name

            RunnerLog(
                self.task,
                self.run_id,
                10,
                f"{file_size(uploaded_size)} uploaded to {server_name} server.",
            )

            return smb_path

        # pylint: disable=broad-except
        except Exception as e:
            raise RunnerException(
                self.task, self.run_id, 10, f"Failed to save file on server.\n{e}"
            )
