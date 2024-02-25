from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields import EmailField
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    post_image = FileField('Image', validators=[FileAllowed(['jpg', 'png'])])
    # author = StringField('Author', validators=[DataRequired()])
    submit = SubmitField('Post')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SubscribeForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField('Subscribe')
    # Add an id to the CSRF token field
    class Meta:
        csrf_field_name = 'csrf_token'
        csrf_token_id = 'csrf_token'

class WeatherForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    submit = SubmitField('Get Weather')

class BillboardForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')