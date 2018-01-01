from datetime import datetime

from flask_wtf import Form
from wtforms import SubmitField
from wtforms.fields.html5 import DecimalField, DateField
from wtforms.validators import InputRequired, Length, DataRequired, Optional, NumberRange


class BodyCompForm(Form):
    date = DateField("Recorded on", format="%Y-%m-%d",
                     default=datetime.today,
                     validators=[DataRequired()])
    weight = DecimalField("Body weight", validators=[DataRequired()])
    body_fat = DecimalField("Body fat percentage", validators=[Optional(), NumberRange(min=0, max=50)])
    chest = DecimalField("Chest Circumference", validators=[Optional()])
    arm = DecimalField("Arm Circumference", validators=[Optional()])
    waist = DecimalField("Waist Circumference", validators=[Optional()])
    belly = DecimalField("Belly Circumference", validators=[Optional()])
    thigh = DecimalField("Thigh Circumference", validators=[Optional()])
    calf = DecimalField("Calf Circumference", validators=[Optional()])
    forearm = DecimalField("Forearm Circumference", validators=[Optional()])
    submit = SubmitField('Save')
