"""Extract Management 2.0 Data Model.

Model resides in EM Web, but must be copied to :obj:`em_scheduler` and
:obj:`em_runner` before running app.

Database migrations are run through a manager script.

.. code-block:: console

    export FLASK_APP=em_web
    flask db migrate
    flask db upgrade

Sometimes there is a conflict between flask-migrations (Alembic migrations)
and the Postgresql db - Postgres will add some indexes that flask-migrations
doesn't think exist yet.

When this happens just remove the index from the migration file onto the previous
migrations file - so flask-migrations think it has already applied the migration.

"""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime
from dataclasses import dataclass

from sqlalchemy.sql import func

from .extensions import db


@dataclass
class LoginType(db.Model):
    """Lookup table of user login types."""

    __tablename__ = "login_type"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    login = db.relationship("Login", backref="login_type", lazy=True)


@dataclass
class Login(db.Model):
    """Table should contain all login attempts."""

    __tablename__ = "login"
    id: int
    username: str
    login_date: datetime.datetime

    id = db.Column(db.Integer, primary_key=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey(LoginType.id), nullable=True)
    username = db.Column(db.String(120), nullable=False)
    login_date = db.Column(db.DateTime, server_default=func.now())


@dataclass
class User(db.Model):
    """Table containing any user-specific information."""

    # pylint: disable=too-many-instance-attributes

    id: int
    account_name: str
    email: str
    full_name: str
    first_name: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    account_name = db.Column(db.String(200), nullable=True, index=True)
    email = db.Column(db.String(200), nullable=True, index=True)
    full_name = db.Column(db.String(200), nullable=True)
    first_name = db.Column(db.String(200), nullable=True)
    project_owner = db.relationship(
        "Project", backref="project_owner", lazy=True, foreign_keys="Project.owner_id"
    )
    project_creator = db.relationship(
        "Project",
        backref="project_creator",
        lazy=True,
        foreign_keys="Project.creator_id",
    )
    project_updater = db.relationship(
        "Project",
        backref="project_updater",
        lazy=True,
        foreign_keys="Project.updater_id",
    )
    task_creator = db.relationship(
        "Task", backref="task_creator", lazy=True, foreign_keys="Task.creator_id"
    )
    task_updater = db.relationship(
        "Task", backref="task_updater", lazy=True, foreign_keys="Task.updater_id"
    )
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def get_id(self):
        """Convert id to unicode."""
        return str(self.id).encode("utf-8").decode("utf-8")


@dataclass
class Project(db.Model):
    """Table containing project details."""

    # pylint: disable=too-many-instance-attributes

    id: int
    name: str
    description: str
    owner_id: int
    cron: int
    cron_year: int
    cron_month: int
    cron_week: int
    cron_day: int
    cron_week_day: int
    cron_hour: int
    cron_min: int
    cron_sec: int
    cron_start_date: datetime.datetime
    cron_end_date: datetime.datetime

    intv: int
    intv_type: str
    intv_value: int
    intv_start_date: datetime.datetime
    intv_end_date: datetime.datetime

    ooff: int
    ooff_date: datetime.datetime

    created: datetime.datetime
    creator_id: int
    updated: datetime.datetime
    updater_id: int

    global_params: str

    sequence_tasks: int

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(8000), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True, index=True)

    cron = db.Column(db.Integer, nullable=True)
    cron_year = db.Column(db.Integer, nullable=True)
    cron_month = db.Column(db.Integer, nullable=True)
    cron_week = db.Column(db.Integer, nullable=True)
    cron_day = db.Column(db.Integer, nullable=True)
    cron_week_day = db.Column(db.Integer, nullable=True)
    cron_hour = db.Column(db.Integer, nullable=True)
    cron_min = db.Column(db.Integer, nullable=True)
    cron_sec = db.Column(db.Integer, nullable=True)
    cron_start_date = db.Column(db.DateTime, nullable=True)
    cron_end_date = db.Column(db.DateTime, nullable=True)

    intv = db.Column(db.Integer, nullable=True)
    intv_type = db.Column(db.String(5), nullable=True)
    intv_value = db.Column(db.Integer, nullable=True)
    intv_start_date = db.Column(db.DateTime, nullable=True)
    intv_end_date = db.Column(db.DateTime, nullable=True)

    ooff = db.Column(db.Integer, nullable=True)
    ooff_date = db.Column(db.DateTime, nullable=True)

    global_params = db.Column(db.String(8000), nullable=True)

    sequence_tasks = db.Column(db.Integer, nullable=True)

    task = db.relationship(
        "Task",
        backref="project",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )

    created = db.Column(db.DateTime, server_default=func.now())
    creator_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )
    updated = db.Column(db.DateTime, onupdate=func.now())
    updater_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )


@dataclass
class TaskSourceType(db.Model):
    """Lookup table of task source types."""

    __tablename__ = "task_source_type"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    task = db.relationship("Task", backref="source_type", lazy=True)


@dataclass
class TaskSourceQueryType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_source_query_type"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    task = db.relationship("Task", backref="query_type", lazy=True)


@dataclass
class TaskProcessingType(db.Model):
    """Lookup table of task query source types."""

    __tablename__ = "task_processing_type"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    task = db.relationship("Task", backref="processing_type", lazy=True)


@dataclass
class TaskStatus(db.Model):
    """Lookup table of task status types.

    This table can link back to a task status, or a task log status.
    """

    __tablename__ = "task_status"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=True)
    task = db.relationship(
        "Task",
        backref="status",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )
    task_log = db.relationship(
        "TaskLog",
        backref="status",
        lazy="dynamic",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


@dataclass
class Connection(db.Model):
    """Table containing all destination information."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection"
    id: int
    name: str
    description: str
    address: str
    primary_contact: str
    primary_contact_email: str
    primary_contact_phone: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(120), nullable=True)
    primary_contact = db.Column(db.String(400), nullable=True)
    primary_contact_email = db.Column(db.String(120), nullable=True)
    primary_contact_phone = db.Column(db.String(120), nullable=True)
    ssh = db.relationship(
        "ConnectionSsh",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSsh.connection_id",
    )
    sftp = db.relationship(
        "ConnectionSftp",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSftp.connection_id",
    )
    ftp = db.relationship(
        "ConnectionFtp",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionFtp.connection_id",
    )
    smb = db.relationship(
        "ConnectionSmb",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionSmb.connection_id",
    )
    database = db.relationship(
        "ConnectionDatabase",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionDatabase.connection_id",
    )
    gpg = db.relationship(
        "ConnectionGpg",
        backref="connection",
        lazy=True,
        foreign_keys="ConnectionGpg.connection_id",
    )


@dataclass
class ConnectionSftp(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_sftp"
    id: int
    connection_id: int
    name: str
    address: str
    port: int
    path: str
    username: str
    key: str
    password: str
    task: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=False, index=True
    )
    name = db.Column(db.String(500), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    port = db.Column(db.Integer, nullable=True)
    path = db.Column(db.String(500), nullable=False)
    username = db.Column(db.String(120), nullable=True)
    key = db.Column(db.String(8000), nullable=True)
    password = db.Column(db.Text, nullable=False)
    task = db.relationship(
        "Task",
        backref="destination_sftp_conn",
        lazy=True,
        foreign_keys="Task.destination_sftp_id",
    )
    task_source = db.relationship(
        "Task",
        backref="source_sftp_conn",
        lazy=True,
        foreign_keys="Task.source_sftp_id",
    )
    query_source = db.relationship(
        "Task", backref="query_sftp_conn", lazy=True, foreign_keys="Task.query_sftp_id"
    )
    processing_source = db.relationship(
        "Task",
        backref="processing_sftp_conn",
        lazy=True,
        foreign_keys="Task.processing_sftp_id",
    )


@dataclass
class ConnectionSsh(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_ssh"
    id: int
    connection_id: int
    name: str
    address: str
    port: int
    username: str
    password: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=False, index=True
    )
    name = db.Column(db.String(500), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    port = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(120), nullable=False)
    password = db.Column(db.Text, nullable=False)
    task_source = db.relationship(
        "Task",
        backref="source_ssh_conn",
        lazy=True,
        foreign_keys="Task.source_ssh_id",
    )


@dataclass
class ConnectionGpg(db.Model):
    """Table conntaining gpg keys."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_gpg"
    id: int
    connection_id: int
    name: str
    key: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=False, index=True
    )
    name = db.Column(db.String(500), nullable=False)
    key = db.Column(db.String(8000), nullable=True)
    task_source = db.relationship(
        "Task",
        backref="file_gpg_conn",
        lazy=True,
        foreign_keys="Task.file_gpg_id",
    )


@dataclass
class ConnectionFtp(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_ftp"
    id: int
    connection_id: int
    name: str
    address: str
    path: str
    username: str
    password: str
    task: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=False, index=True
    )
    name = db.Column(db.String(500), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    username = db.Column(db.String(500), nullable=False)
    password = db.Column(db.Text, nullable=False)
    task = db.relationship(
        "Task",
        backref="destination_ftp_conn",
        lazy=True,
        foreign_keys="Task.destination_ftp_id",
    )
    task_source = db.relationship(
        "Task", backref="source_ftp_conn", lazy=True, foreign_keys="Task.source_ftp_id"
    )
    query_source = db.relationship(
        "Task", backref="query_ftp_conn", lazy=True, foreign_keys="Task.query_ftp_id"
    )
    processing_source = db.relationship(
        "Task",
        backref="processing_ftp_conn",
        lazy=True,
        foreign_keys="Task.processing_ftp_id",
    )


@dataclass
class ConnectionSmb(db.Model):
    """Table conntaining sftp connection strings."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "connection_smb"
    id: int
    connection_id: int
    name: str
    share_name: str
    path: str
    username: str
    password: str
    server_ip: str
    server_name: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=False, index=True
    )
    name = db.Column(db.String(120), nullable=False)
    share_name = db.Column(db.String(500), nullable=False)
    path = db.Column(db.String(1000), nullable=False)
    username = db.Column(db.String(500), nullable=False)
    password = db.Column(db.Text, nullable=False)
    server_ip = db.Column(db.String(500), nullable=False)
    server_name = db.Column(db.String(500), nullable=False)
    task = db.relationship(
        "Task",
        backref="destination_smb_conn",
        lazy=True,
        foreign_keys="Task.destination_smb_id",
    )
    task_source = db.relationship(
        "Task", backref="source_smb_conn", lazy=True, foreign_keys="Task.source_smb_id"
    )
    query_source = db.relationship(
        "Task", backref="query_smb_conn", lazy=True, foreign_keys="Task.query_smb_id"
    )
    processing_source = db.relationship(
        "Task",
        backref="processing_smb_conn",
        lazy=True,
        foreign_keys="Task.processing_smb_id",
    )


@dataclass
class ConnectionDatabaseType(db.Model):
    """Lookup table of task source database types."""

    __tablename__ = "connection_database_type"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    database = db.relationship("ConnectionDatabase", backref="database_type", lazy=True)


@dataclass
class ConnectionDatabase(db.Model):
    """List of task source databases and connection strings."""

    __tablename__ = "connection_database"
    id: int
    type_id: int
    name: str
    connection_string: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    type_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionDatabaseType.id), nullable=False, index=True
    )
    connection_id = db.Column(
        db.Integer, db.ForeignKey(Connection.id), nullable=False, index=True
    )
    name = db.Column(db.String(500), nullable=False)
    connection_string = db.Column(db.Text, nullable=False)
    task_source = db.relationship(
        "Task",
        backref="source_database_conn",
        lazy=True,
        foreign_keys="Task.source_database_id",
    )


@dataclass
class TaskDestinationFileType(db.Model):
    """Lookup table of task destination file types."""

    __tablename__ = "task_destination_file_type"
    id: int
    name: str
    ext: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    ext = db.Column(db.String(120), nullable=False)
    task = db.relationship("Task", backref="file_type", lazy=True)


@dataclass
class QuoteLevel(db.Model):
    """Lookup table for python quote levels."""

    __tablename__ = "quote_level"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    task = db.relationship("Task", backref="destination_file_quote_level", lazy=True)


@dataclass
class Task(db.Model):
    """Table containing task details."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "task"
    # general information
    id: int
    name: str
    project_id: int
    status_id: int
    enabled: int
    order: int
    last_run: datetime.datetime
    next_run: datetime.datetime
    last_run_job_id: str
    created: datetime.datetime
    creator_id: int
    updated: datetime.datetime
    updater_id: int

    # data source
    source_type_id: int
    source_database_id: int

    source_query_type_id: int
    source_query_include_header: int
    source_git: str
    source_url: str
    source_code: str

    query_smb_id: int
    query_smb_file: str
    query_sftp_id: int
    query_sftp_file: str
    query_ftp_id: int
    query_ftp_file: str
    query_params: str

    source_smb_delimiter: str
    source_smb_ignore_delimiter: int
    source_smb_file: str
    source_smb_id: int

    source_ftp_file: str
    source_ftp_delimiter: str
    source_ftp_ignore_delimiter: int
    source_ftp_id: int

    source_sftp_file: str
    source_sftp_delimiter: str
    source_sftp_ignore_delimiter: int
    source_sftp_id: int

    source_ssh_id: int

    # processing
    processing_type_id: int
    processing_smb_id: int
    processing_smb_file: str
    processing_sftp_id: int
    processing_sftp_file: str
    processing_ftp_id: int
    processing_ftp_file: str
    processing_code: str
    processing_url: str
    processing_git: str
    processing_command: str

    # destination
    destination_file_delimiter: str
    destination_file_name: str
    destination_ignore_delimiter: int
    destination_file_line_terminator: str
    destination_quote_level_id: int

    destination_create_zip: int
    destination_zip_name: str

    destination_file_type_id: int

    destination_sftp: int
    destination_sftp_overwrite: int
    destination_sftp_id: int

    destination_ftp: int
    destination_ftp_overwrite: int
    destination_ftp_id: int

    destination_smb: int
    destination_smb_overwrite: int
    destination_smb_id: int

    file_gpg: int
    file_gpg_id: int

    email_completion: int
    email_completion_log: int
    email_completion_file: int
    email_completion_file_embed: int
    email_completion_dont_send_empty_file: int
    email_completion_recipients: str
    email_completion_message: str

    email_error: int
    email_error_recipients: str
    email_error_message: str

    max_retries: int

    est_duration: int

    # general information
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(1000), nullable=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey(Project.id), nullable=True, index=True
    )
    status_id = db.Column(
        db.Integer, db.ForeignKey(TaskStatus.id), nullable=True, index=True
    )
    enabled = db.Column(db.Integer, nullable=True, index=True)
    order = db.Column(db.Integer, nullable=True, index=True)
    last_run = db.Column(db.DateTime, nullable=True)
    last_run_job_id = db.Column(db.String(30), nullable=True, index=True)
    next_run = db.Column(db.DateTime, nullable=True, index=True)
    created = db.Column(db.DateTime, server_default=func.now(), index=True)
    creator_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )
    updated = db.Column(db.DateTime, onupdate=func.now(), index=True)
    updater_id = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, index=True
    )

    """ data source """
    # db/sftp/smb/ftp
    source_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskSourceType.id), nullable=True, index=True
    )

    # source locations

    # git/url/code/sftp/ftp/smb
    source_query_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskSourceQueryType.id), nullable=True, index=True
    )
    source_query_include_header = db.Column(db.Integer, nullable=True)

    # source git
    source_git = db.Column(db.String(1000), nullable=True)

    # source web url
    source_url = db.Column(db.String(1000), nullable=True)

    # source typed code
    source_code = db.Column(db.String(8000), nullable=True)

    query_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    query_smb_file = db.Column(db.String(1000), nullable=True)

    query_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    query_sftp_file = db.Column(db.String(1000), nullable=True)

    query_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    query_ftp_file = db.Column(db.String(1000), nullable=True)

    query_params = db.Column(db.String(8000), nullable=True)

    # source smb sql file
    source_smb_file = db.Column(db.String(1000), nullable=True)
    source_smb_delimiter = db.Column(db.String(10), nullable=True)
    source_smb_ignore_delimiter = db.Column(db.Integer, nullable=True)
    source_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )

    # source ftp sql file
    source_ftp_file = db.Column(db.String(1000), nullable=True)
    source_ftp_delimiter = db.Column(db.String(10), nullable=True)
    source_ftp_ignore_delimiter = db.Column(db.Integer, nullable=True)
    source_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )

    # source sftp sql file
    source_sftp_file = db.Column(db.String(1000), nullable=True)
    source_sftp_delimiter = db.Column(db.String(10), nullable=True)
    source_sftp_ignore_delimiter = db.Column(db.Integer, nullable=True)
    source_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )

    # source database
    source_database_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionDatabase.id), nullable=True, index=True
    )

    source_ssh_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSsh.id), nullable=True, index=True
    )

    """ processing script source """

    processing_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskProcessingType.id), nullable=True, index=True
    )

    processing_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )
    processing_smb_file = db.Column(db.String(1000), nullable=True)

    processing_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    processing_sftp_file = db.Column(db.String(1000), nullable=True)

    processing_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )
    processing_ftp_file = db.Column(db.String(1000), nullable=True)

    processing_code = db.Column(db.String(8000), nullable=True)
    processing_url = db.Column(db.String(1000), nullable=True)
    processing_git = db.Column(db.String(1000), nullable=True)

    processing_command = db.Column(db.String(1000), nullable=True)

    """ destination """

    # destination file
    destination_file_name = db.Column(db.String(1000), nullable=True)
    destination_file_delimiter = db.Column(db.String(10), nullable=True)
    destination_ignore_delimiter = db.Column(db.Integer, nullable=True)
    destination_file_line_terminator = db.Column(db.String(10), nullable=True)

    # destination zip archive
    destination_create_zip = db.Column(db.Integer, nullable=True)
    destination_zip_name = db.Column(db.String(1000), nullable=True)

    # csv/txt/other
    destination_file_type_id = db.Column(
        db.Integer, db.ForeignKey(TaskDestinationFileType.id), nullable=True, index=True
    )

    # save to sftp server
    destination_sftp = db.Column(db.Integer, nullable=True, index=True)
    destination_sftp_overwrite = db.Column(db.Integer, nullable=True)
    destination_sftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSftp.id), nullable=True, index=True
    )
    # save to ftp server
    destination_ftp = db.Column(db.Integer, nullable=True, index=True)
    destination_ftp_overwrite = db.Column(db.Integer, nullable=True)
    destination_ftp_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionFtp.id), nullable=True, index=True
    )

    # save to smb server
    destination_smb = db.Column(db.Integer, nullable=True, index=True)
    destination_smb_overwrite = db.Column(db.Integer, nullable=True)
    destination_smb_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionSmb.id), nullable=True, index=True
    )

    file_gpg = db.Column(db.Integer, nullable=True, index=True)
    file_gpg_id = db.Column(
        db.Integer, db.ForeignKey(ConnectionGpg.id), nullable=True, index=True
    )

    destination_quote_level_id = db.Column(
        db.Integer, db.ForeignKey(QuoteLevel.id), nullable=True, index=True
    )

    """ email """
    # completion email
    email_completion = db.Column(db.Integer, nullable=True, index=True)
    email_completion_log = db.Column(db.Integer, nullable=True)
    email_completion_file = db.Column(db.Integer, nullable=True)
    email_completion_file_embed = db.Column(db.Integer, nullable=True)
    email_completion_recipients = db.Column(db.String(1000), nullable=True)
    email_completion_message = db.Column(db.String(8000), nullable=True)
    email_completion_dont_send_empty_file = db.Column(db.Integer, nullable=True)

    # error email
    email_error = db.Column(db.Integer, nullable=True, index=True)
    email_error_recipients = db.Column(db.String(1000), nullable=True)
    email_error_message = db.Column(db.String(8000), nullable=True)

    # rerun on fail
    max_retries = db.Column(db.Integer, nullable=True, index=True)

    est_duration = db.Column(db.Integer, nullable=True, index=True)

    # tasklog link
    task = db.relationship(
        "TaskLog",
        backref="task",
        lazy=True,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


@dataclass
class TaskLog(db.Model):
    """Table containing job run history."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = "task_log"
    id: int
    task_id: int
    status_id: int
    job_id: str
    message: str
    status_date: datetime.datetime

    job_id = db.Column(db.String(1000), nullable=True, index=True)
    id = db.Column(db.Integer, primary_key=True, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=True, index=True)
    status_id = db.Column(
        db.Integer, db.ForeignKey(TaskStatus.id), nullable=True, index=True
    )
    message = db.Column(db.Text, nullable=True)
    status_date = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    error = db.Column(db.Integer, nullable=True, index=True)

    __table_args__ = (
        db.Index("ix_task_log_status_date_error", "status_date", "error"),
    )


@dataclass
class TaskFile(db.Model):
    """Table containing paths to task backup files."""

    __tablename__ = "task_file"
    id: int
    name: str
    task_id: int
    job_id: str
    size: str
    file_hash: str
    path: str
    created: datetime.datetime

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(1000), nullable=True, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=True, index=True)
    job_id = db.Column(db.String(1000), nullable=True, index=True)
    size = db.Column(db.String(200), nullable=True, index=True)
    path = db.Column(db.String(1000), nullable=True, index=True)
    file_hash = db.Column(db.String(1000), nullable=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now, index=True)

    __table_args__ = (
        db.Index("ix_task_file_id_task_id_job_id", "id", "task_id", "job_id"),
    )
