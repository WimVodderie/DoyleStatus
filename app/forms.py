from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired
from wtforms import DateField

import datetime


class HistoryForm(FlaskForm):
    serverName = SelectField("Server name", choices=[])
    submit = SubmitField("Display")


class ChartForm(FlaskForm):
    startDate = DateField("Date", format="%Y-%m-%d", default=datetime.date.min)
    submit = SubmitField("Update")
