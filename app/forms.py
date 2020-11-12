from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms import DateField

import datetime

class HistoryForm(FlaskForm):
    servername = StringField("Servername", validators=[DataRequired()])
    submit = SubmitField("Display")


class ChartForm(FlaskForm):
    startDate = DateField('Date', format='%Y-%m-%d', default=datetime.datetime(2020,11,11,0,0,0))
    submit = SubmitField("Update")
