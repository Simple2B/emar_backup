from datetime import datetime

from sqlalchemy.orm import relationship

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from markupsafe import Markup

from app import db

from app.models.utils import ModelMixin, RowActionListMixin, BlobMixin, BlobUploadField
from app.utils import MyModelView

from config import BaseConfig as CFG


class DesktopClient(db.Model, ModelMixin, BlobMixin):

    __tablename__ = "desktop_clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    version = db.Column(db.String(64))
    # msi_path = db.Column(db.LargeBinary or db.String)  # TODO Could we store it on SFTP server?
    description = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.now)

    flag = relationship("ClientVersion", passive_deletes=True)
    flag_name = db.Column(
        db.String, db.ForeignKey("client_versions.name", ondelete="CASCADE")
    )

    def __repr__(self):
        return self.name

    def __unicode__(self):
        return "name : {name}; filename : {filename})".format(
            name=self.name, filename=self.filename
        )


class DesktopClientView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "DesktopClientView"

    list_template = "import-admin-list-to-dashboard.html"

    column_searchable_list = ["name", "version", "flag_name"]

    column_list = (
        "name",
        "version",
        "flag_name",
        "description",
        "filename",
        "download",
    )
    form_excluded_columns = ("mimetype", "size", "filename")

    form_extra_fields = {
        "blob": BlobUploadField(
            label="File",
            allowed_extensions=["msi"],
            size_field="size",
            filename_field="filename",
            mimetype_field="mimetype",
        )
    }

    column_filters = ("name", "version",  "flag_name", "description", "filename",)
    action_disallowed_list = ["delete"]

    def _download_formatter(self, context, model, name):
        return Markup(
            "<a href='{url}' target='_blank'>Download</a>".format(
                url=self.get_url("download_msi.download_msi", id=model.id)
            )
        )

    column_formatters = {
        "download": _download_formatter,
    }

    def edit_form(self, obj):
        form = super(DesktopClientView, self).edit_form(obj)

        versions = [i.version for i in DesktopClient.query.all()]

        for version in versions:
            if (version, version) not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append((version, version))

        query_res = self.session.query(DesktopClient).all()

        # TODO check wich option works better
        # from app.models import ComputerView
        # msi_versions = [i[0] for i in ComputerView.form_choices["msi_version"]]
        # for version in [i.version for i in query_res]:
        #     if version in msi_versions:
        #         break
        #     print(f"{version} added")
        #     ComputerView.form_choices["msi_version"].append((version, f"{version}"))
        # print(f"msi_versions updated {msi_versions}")

        form.version.query = query_res
        return form

    def _can_edit(self, model):
        # return True to allow edit
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def _can_delete(self, model):
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def allow_row_action(self, action, model):

        if isinstance(action, EditRowAction):
            return self._can_edit(model)

        if isinstance(action, DeleteRowAction):
            return self._can_delete(model)

        # otherwise whatever the inherited method returns
        return super().allow_row_action(action, model)

    # list rows depending on current user permissions
    def get_query(self):
        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
                result_query = self.session.query(self.model)
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False
                result_query = self.session.query(self.model).filter(
                    self.model.name == "None"
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.name == "None"
            )
        return result_query
