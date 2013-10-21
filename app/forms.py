from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField,SelectField, DateField, TextAreaField,IntegerField
from wtforms.validators import Required

class LoginForm(Form):
    staffID = TextField('ID', validators = [Required()])
    password = PasswordField('pass', validators= [Required()])

class ForgotPassword(Form):
    staffID = TextField('staffID', validators = [Required()])
    email = TextField('emailID', validators = [Required()])

class PassForm(Form):
    current = PasswordField('old', validators = [Required()])
    password = PasswordField('pass', validators= [Required()])
    confirm = PasswordField('confirm', validators = [Required()])

class StaffForm(Form):
    name = TextField('name', validators = [Required()])
    address = TextAreaField('address', validators = [Required()])
    gender = SelectField('Gender', choices=[('1', 'M'), ('2', 'F')])
    dob = DateField('dob', validators = [Required()], format='%Y-%m-%d')
    contact = IntegerField('contact', validators = [Required()])
    temp_pass = TextField('temp_pass')