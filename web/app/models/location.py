from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import relationship

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.controllers import MyModelView

from .user import UserView


class Location(db.Model, ModelMixin):

    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    company = relationship("Company", passive_deletes=True, backref='locations', lazy='select')
    company_name = db.Column(db.String, db.ForeignKey("companies.name", ondelete="CASCADE"))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class LocationView(RowActionListMixin, MyModelView):
    can_delete = True
    column_hide_backrefs = False
    column_list = ["id", "name", "company_name", "created_at"]
    column_searchable_list = ["name", "company_name"]

    def edit_form(self, obj):
        form = super(LocationView, self).edit_form(obj)

        query_res = self.session.query(Location).all()

        permissions = [i[0] for i in UserView.form_choices['asociated_with']]
        for location in [i.name for i in query_res]:
            if location in permissions:
                break
            print(f"{location} added")
            UserView.form_choices['asociated_with'].append((location, f"Location-{location}"))
        print(f"permissions updated {permissions}")

        form.name.query = query_res
        return form

    def _can_edit(self, model):
        # return True to allow edit
        return True
        # print("current_user", current_user.username, current_user.asociated_with)
        # if current_user.asociated_with == "global-full":
        #     return True
        # else:
        #     return False

    def _can_delete(self, model):
        print("current_user", current_user.username, current_user.asociated_with)
        if current_user.asociated_with == "global-full":
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
        print("location get_query current_user", current_user, current_user.asociated_with)
        if current_user:
            user_permission: str = current_user.asociated_with
            if user_permission.lower() == "global-full" or user_permission.lower() == "global-view":
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(
                    or_(
                        self.model.name == user_permission,
                        self.model.company_name == user_permission
                    )
                )
        else:
            result_query = self.session.query(self.model).filter(self.model.computer_name == "None")
        return result_query
