from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .db_models import User, Post
from flask_login import current_user

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])

    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    profile_image = FileField('Select Profile Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Sign Up')

    # 이미 사용중인 아이디인지 확인
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('이 아이디는 이미 사용 중입니다.')

    # 이미 사용중인 이메일인지 확인
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('이 이메일은 이미 사용 중입니다.')     

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')# Chrome process가 모두 꺼졌다가 다시 켜졌을 때 동작 확인
    submit = SubmitField('Sign In')

class UpdateAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_image = FileField('Select Profile Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Update')
    
    # 이미 사용중인 이메일인지 확인
    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('이 이메일은 이미 사용 중입니다.') 

class PostForm(FlaskForm):
    result = RadioField('탈출하셨나요?', choices=[('success', '성공'), ('failure', '실패')], default='success')
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=60)], render_kw={"placeholder": "테마 이름"})
    content = TextAreaField('Content', validators=[DataRequired()], render_kw={"placeholder": "후기를 입력하세요"})
    post_image = FileField('Select Post Image', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Post')