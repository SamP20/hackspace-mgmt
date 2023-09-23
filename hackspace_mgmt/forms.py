from wtforms import Field, widgets, fields
from wtforms.validators import DataRequired
from flask_admin import form
from flask import url_for, flash, session
from sqlalchemy.exc import NoResultFound

from hackspace_mgmt.models import db, Card, Member

class SerialField(Field):
    """
    A text field, except all input is coerced to an integer.  Erroneous input
    is ignored and will not be accepted as a value.
    """

    widget = widgets.TextInput()

    def __init__(self, label=None, validators=None, suppress_enter=True, render_kw=None, **kwargs):
        if suppress_enter:
            render_kw = render_kw or {}
            render_kw["data-suppress-enter"] = "1"
        super().__init__(label, validators, render_kw=render_kw, **kwargs)

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        if self.data is not None:
            return f'{self.data:x}'
        return ""

    def process_formdata(self, valuelist):
        if not valuelist:
            return

        try:
            self.data = int(valuelist[0], 16)
        except ValueError as exc:
            self.data = None
            raise ValueError(self.gettext("Not a valid serial number.")) from exc

def card_serial_formatter(view, context, model, name):
    if model.card_serial:
        return f"{model.card_serial:x}"
    else:
        return ""

class ViewHelperJsMixin():
    def render(self, template, **kwargs):
        """
        using extra js in render method allow use
        url_for that itself requires an app context
        """
        self.extra_js = [url_for("static", filename="js/helpers.js")]

        return super().render(template, **kwargs)


class CardLoginForm(form.SecureForm):
    serial_number = SerialField(
        'Remove card/fob from wallet (if applicable) and scan to enter serial number',
        suppress_enter=False,
        render_kw={"autofocus": "1", "autocomplete": "off"},
        description="Removing from wallet is required to avoid accidentally scanning the wrong card",
        validators=[DataRequired()],
    )

    intermediate = False

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        card_select = db.select(Card).where(Card.card_serial==self.serial_number.data)
        card_select = card_select.join(Card.member)
        try:
            card = db.session.execute(card_select).scalar_one()
            self.member = card.member
            session["member_id"] = self.member.id
            flash(f'Hello {self.member.display_name}', 'success')
        except NoResultFound:
            self.serial_number.errors.append("Invalid card. Have you enrolled it yet?")
            self.serial_number.raw_data = None
            self.serial_number.data = None
            return False

        return True