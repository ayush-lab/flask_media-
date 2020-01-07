from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired, Email, Length

class loginForm(FlaskForm):
	username=StringField("Username", validators=[DataRequired()])
	password=PasswordField("Password",validators=[DataRequired()])
	remember_me =BooleanField('Remember_me')
	submit=SubmitField("LOGIN IN")

class registerForm(FlaskForm):
	email=StringField("Email",validators=[DataRequired(), Email(message ="invalid email")] )
	username=StringField("Username", validators=[DataRequired()])
	password=PasswordField("Password", validators=[DataRequired()])
	remember_me =BooleanField('Remember_me')
	submit=SubmitField("Sign In")

class EditProfile(FlaskForm):
	username= StringField("Username", validators =[DataRequired()])
	about_me=TextAreaField("About_me", validators=[Length(min=0, max=140)])
	submit = SubmitField('Submit')

class PostForm(FlaskForm):
	post=  TextAreaField("Say something  ",validators=[DataRequired(), Length(min=1, max=340)])
	submit = SubmitField('Submit')

'''
{% if current_user.is_authenticated %}
{% elif user!=current_user  %}
	please login first to access the HOME page. click here to login in <a href="{{url_for('login')}}">login</a>.
	{% endif %}
'''