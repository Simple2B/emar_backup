from flask_admin.contrib.sqla import ModelView
from flask_login import current_user


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def __repr__(self):
        return "MyModelView"
