from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email
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
