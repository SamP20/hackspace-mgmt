
from wtforms import fields
from wtforms.validators import EqualTo, DataRequired
from flask import flash, redirect, request, url_for, session
from flask_admin import form, Admin, BaseView, expose
from flask_admin.helpers import get_redirect_target, validate_form_on_submit
from hackspace_mgmt.models import db, Machine, LegacyMachineAuth, Induction
from hackspace_mgmt.forms import SerialField, CardLoginForm
from sqlalchemy.exc import IntegrityError

class MachineForm(form.SecureForm):
    machine = fields.SelectField("Machine", validators=[DataRequired()])

    intermediate = True

class PasswordForm(form.SecureForm):
    password = fields.StringField(
        "",
        validators=[DataRequired()],
        render_kw={"autocomplete": "off"},
        description="This is to prove you have been previously inducted"
    )

    intermediate = True

    def __init__(self, *args, pass_label="", **kwargs):
        super().__init__(*args, **kwargs)
        self.password.label.text = session["machine"] + " " + pass_label

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        machine = db.session.query(Machine).get(session["machine_id"])
        if machine.legacy_password != self.password.data:
            self.password.errors.append("Incorrect password")
            return False
        return True


class CardSerialForm(form.SecureForm):
    serial_number = SerialField(
        'Remove card/fob from wallet (if applicable) and scan to enter serial number',
        suppress_enter=False,
        render_kw={"autofocus": "1", "autocomplete": "off"},
        description="Removing from wallet is required to avoid accidentally scanning the wrong card",
        validators=[DataRequired()],
    )

    intermediate = False


class SelfInductionView(BaseView):
    title = "Machine self-induction"

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        return_url = get_redirect_target() or self.get_url('.index')

        form = CardLoginForm(request.form)
        if validate_form_on_submit(form):
            return redirect(url_for(".machine"))
        return self.render('multipage_form.html', return_url=return_url, form=form, title=self.title)

    @expose('/machine', methods=('GET', 'POST'))
    def machine(self):
        return_url = get_redirect_target() or self.get_url('.index')

        form = MachineForm(request.form)
        machines = db.session.query(Machine).filter(Machine.legacy_auth!=LegacyMachineAuth.none).all()
        form.machine.choices = [(m.id, m.name) for m in machines]

        if validate_form_on_submit(form):
            machine_id = int(form.machine.data)
            machine = [m for m in machines if m.id == machine_id][0]

            session["machine_id"] = machine_id
            session["machine"] = machine.name

            return redirect(url_for(".password"))

        return self.render('multipage_form.html', return_url=return_url, form=form, title=self.title)

    @expose('/password', methods=('GET', 'POST'))
    def password(self):
        return_url = get_redirect_target() or self.get_url('.index')

        machine = db.session.query(Machine).get(session["machine_id"])

        if machine.legacy_auth == LegacyMachineAuth.password:
            pass_label = "login password"
        elif machine.legacy_auth == LegacyMachineAuth.padlock:
            pass_label = "padlock code"
        else:
            pass_label = "secret"

        form = PasswordForm(request.form, pass_label=pass_label)
        if validate_form_on_submit(form):
            machine = session["machine"]
            induction = Induction(
                member_id = session["member_id"],
                machine_id = session["machine_id"]
            )
            db.session.add(induction)
            try:
                db.session.commit()
                flash(f'Successfully inducted for the {machine}', 'success')
            except IntegrityError:
                flash(f'Already inducted for the {machine}', 'error')
            return redirect(url_for("general.index"))
        return self.render('multipage_form.html', return_url=return_url, form=form, title=self.title)

    @expose('/padlock', methods=('GET', 'POST'))
    def padlock(self):
        return_url = get_redirect_target() or self.get_url('.index')

        form = PasswordForm(request.form)
        if validate_form_on_submit(form):
            machine = session["machine"]
            induction = Induction(
                member_id = session["member_id"],
                machine_id = session["machine_id"]
            )
            db.session.add(induction)
            try:
                db.session.commit()
                flash(f'Successfully inducted for the {machine}', 'success')
            except IntegrityError:
                flash(f'Already inducted for the {machine}', 'error')
            return redirect(url_for("general.index"))
        return self.render('multipage_form.html', return_url=return_url, form=form, title=self.title)


def create_views(admin: Admin):
    admin.add_view(SelfInductionView("Self induction", endpoint="induct"))