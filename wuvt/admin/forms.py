from flask_wtf import FlaskForm
from wtforms import RadioField

class SettingsForm(FlaskForm):
    form = RadioField("Radiothon", choices=[("off", "OFF"), ("on", "ON")])
