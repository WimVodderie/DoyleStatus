from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms import DateField

import datetime


class HistoryForm(FlaskForm):
    servername = StringField("Servername", default="", validators=[DataRequired()])
    submit = SubmitField("Display")


class ChartForm(FlaskForm):
    startDate = DateField("Date", format="%Y-%m-%d", default=datetime.date.min)
    submit = SubmitField("Update")
