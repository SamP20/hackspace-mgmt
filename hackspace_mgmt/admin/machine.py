from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from hackspace_mgmt.models import db, Machine, MachineController


class MachineView(ModelView):
    column_searchable_list = ['name']
    column_list = ('name', 'legacy_auth', 'legacy_password', 'controllers')
    inline_models = (MachineController,)
    form_excluded_columns = ('inductions',)
    column_formatters = dict()


def create_views(admin: Admin):
    admin.add_view(MachineView(Machine, db.session, category="Access Control"))