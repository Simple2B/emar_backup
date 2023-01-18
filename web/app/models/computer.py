from datetime import datetime

from sqlalchemy.orm import relationship

from flask_admin.contrib.sqla import ModelView

from app import db
from app.models.utils import ModelMixin


class Computer(db.Model, ModelMixin):

    __tablename__ = "computers"

    id = db.Column(db.Integer, primary_key=True)
    computer_name = db.Column(db.String(64), unique=True, nullable=False)

    location = relationship("Location", passive_deletes=True)
    location_name = db.Column(db.String, db.ForeignKey("locations.name", ondelete="CASCADE"), nullable=False)

    type = db.Column(db.String(128))
    alert_status = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)  # TODO do we need this one? Could computer be deactivated?
    created_at = db.Column(db.DateTime, default=datetime.now)

    sftp_host = db.Column(db.String(128))
    sftp_username = db.Column(db.String(64))
    sftp_password = db.Column(db.String(128))
    sftp_folder_path = db.Column(db.String(256))

    folder_password = db.Column(db.String(128))
    download_status = db.Column(db.String(64))
    last_download_time = db.Column(db.DateTime)
    last_time_online = db.Column(db.DateTime)
    identifier_key = db.Column(db.String(128), default="cc8be41a-ed17-4624-aaac-066a6ce1e930")

    company = relationship("Company", passive_deletes=True)
    company_name = db.Column(db.String, db.ForeignKey("companies.name", ondelete="CASCADE"), nullable=False)


class ComputerView(ModelView):
    can_delete = True
    column_hide_backrefs = False
    column_list = [
        "id",
        "computer_name",
        "alert_status",
        "company_name",
        "location_name",
        "type",
        "sftp_host",
        "sftp_username",
        "sftp_password",
        "sftp_folder_path",
        "folder_password",
        "download_status",
        "last_download_time",
        "last_time_online",
        "identifier_key",
        
        "activated",
        "created_at"
        ]
    column_searchable_list = ["company_name", "location_name"]
