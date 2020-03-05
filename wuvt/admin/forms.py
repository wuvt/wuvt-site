from flask_wtf import FlaskForm
from wtforms import RadioField

class SettingsForm(FlaskForm):
    radiothon = RadioField("Radiothon", choices=[("off", "OFF"), ("on", "ON")])
