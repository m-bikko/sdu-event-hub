from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, FloatField, IntegerField, DateTimeLocalField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    sdu_id = StringField('SDU ID (Optional)', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    photo = FileField('Profile Photo (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered. Please choose a different one or login.')
    
    def validate_sdu_id(self, sdu_id):
        if sdu_id.data:
            user = User.query.filter_by(sdu_id=sdu_id.data).first()
            if user:
                raise ValidationError('This SDU ID is already registered.')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login as Admin')

class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    sdu_id = StringField('SDU ID', validators=[Optional(), Length(max=20)])
    photo = FileField('Update Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')
    
    def validate_sdu_id(self, sdu_id):
        if sdu_id.data:
            user = User.query.filter_by(sdu_id=sdu_id.data).first()
            if user and user.id != self.user_id:
                raise ValidationError('This SDU ID is already registered.')

class AddStudentForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    sdu_id = StringField('SDU ID', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[('student', 'Student'), ('club_head', 'Club Head')], default='student')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    photo = FileField('Profile Photo (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Add Student')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered. Please choose a different one.')
    
    def validate_sdu_id(self, sdu_id):
        if sdu_id.data:
            user = User.query.filter_by(sdu_id=sdu_id.data).first()
            if user:
                raise ValidationError('This SDU ID is already registered.')

# Additional forms will be added as needed for other features