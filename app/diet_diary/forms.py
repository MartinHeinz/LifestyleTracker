from flask_wtf import Form
from wtforms import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import PasswordField, StringField, SubmitField, DateTimeField, DateField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, EqualTo, InputRequired, Length

from .. import db
from ..models import Role, User


class SelectDayForm(Form):
    date = DateField("Select Day", id="select_day", validators=[InputRequired()])
    submit = SubmitField('Show')


class AddMealForm(Form):
    name = StringField("Meal Name", id="meal_name", validators=[InputRequired()])
    time = DateTimeField("Meal Time", id="meal_time", format='%HH:%MM:%SS')
    submit = SubmitField('Add')


class CopyMealForm(Form):
    date = DateField("Copy Date", validators=[InputRequired()])
    submit = SubmitField('Copy')

