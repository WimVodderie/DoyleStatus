from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class HistoryForm(FlaskForm):
    servername = StringField('Servername', validators=[DataRequired()])
    submit = SubmitField('Display')
