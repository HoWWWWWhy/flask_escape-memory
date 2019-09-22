from flask import render_template, url_for, flash, redirect, request, abort
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from .db_models import User, Post
from my_app import app, db, bcrypt, admin

from flask_login import login_user, current_user, logout_user, login_required
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
import os

from flask_admin.contrib.fileadmin import FileAdmin
import os.path as op
from .my_functions import generate_filename, save_image, post_to_aws_s3
import secrets

# for Heroku & AWS S3
import json, boto3
from botocore.client import Config

S3_BUCKET = app.config['S3_BUCKET']
ACCESS_KEY = app.config['S3_KEY']
SECRET_KEY = app.config['S3_SECRET']

s3_client = boto3.client('s3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config = Config(signature_version = 's3v4')
)

# 관리자 페이지로 옮기기
@app.route('/show_s3')
def show_s3():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)
    summaries = my_bucket.objects.all()
    my_objects = []
    for summary in summaries:
        my_object = {}
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': summary.key
            },                                  
            ExpiresIn=60
        )
        my_object['key'] = summary.key
        my_object['presigned_url'] = url
        my_objects.append(my_object)
        print(my_objects)
    bucket_policy = s3_client.get_bucket_policy(Bucket=S3_BUCKET)

    return render_template('view_bucket.html', my_bucket=my_bucket, files=my_objects, bucket_policy=bucket_policy)

# preview.js에서 바로 onchange 이벤트 시 s3에 업로드할 때 요청하는 페이지.
@app.route('/sign_s3/')
def sign_s3():
    file_name = request.args.get('file_name')
    file_type = request.args.get('file_type')

    presigned_post = s3_client.generate_presigned_post(
        Bucket = S3_BUCKET,
        Key = file_name,
        Fields = {"acl": "public-read", "Content-Type": file_type},
        Conditions = [
            {"acl": "public-read"},
            {"Content-Type": file_type}
        ],
        ExpiresIn = 600
    )

    return json.dumps({
      'data': presigned_post,
      'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
      #'url': 'https://%s.s3.ap-northeast-2.amazonaws.com/%s' % (S3_BUCKET, file_name)
    })

# Admin Page
administrator_list = ["howwwwwhy"]
category_db = "DATABASE"
# category_files = "IMAGE FILES"

class DatabaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username in administrator_list

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if current_user.is_authenticated:
            abort(403)# 403 is "Forbidden" error
        else:
            return redirect(url_for('login', next='/admin'))

class DirectoryView(FileAdmin):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username in administrator_list

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if current_user.is_authenticated:
            abort(403)# 403 is "Forbidden" error
        else:
            return redirect(url_for('login', next='/admin/directory'))

class CleanFilesView(BaseView):
    @expose('/')
    def index(self):
        return self.render('/admin/clean_files.html')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.username in administrator_list

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        if current_user.is_authenticated:
            abort(403)# 403 is "Forbidden" error
        else:        
            return redirect(url_for('login', next='/admin/clean_files'))

admin.add_view(DatabaseView(User, db.session, category=category_db))
admin.add_view(DatabaseView(Post, db.session, category=category_db))

# path_project = op.join(op.dirname(__file__), '/HoWWWWWhy/flask_escape-memory/my_app')
path_project = op.join(op.dirname(__file__), '/')
admin.add_view(DirectoryView(path_project, '/', name="Directory", endpoint='directory'))
# path_profile = op.join(op.dirname(__file__), 'static/profile_images')
# path_post = op.join(op.dirname(__file__), 'static/post_images')
# admin.add_view(FileAdmin(path_profile, '/static/', category=category_files))
# admin.add_view(FileAdmin(path_post, '/static/', category=category_files))

admin.add_view(CleanFilesView(name='Clean Files', endpoint='clean_files'))

@app.route('/admin/clean_files/clean_profile_files')
def clean_profile_files():
    path = op.join(op.dirname(__file__), 'static/profile_images')
    filenames = os.listdir(path)
    used_images_tuple = User.query.with_entities(User.profile_image).all()
    used_images = [used_image[0] for used_image in used_images_tuple]# tuple을 list로 변환
    used_images.append("howwwwwhy.png")# 기본 이미지는 삭제하면 안됨

    for filename in filenames:
        # print(filename)
        if not filename in used_images:
            os.remove(path + '/' + filename)

    return redirect(url_for('clean_files.index'))

@app.route('/admin/clean_files/clean_post_files')
def clean_post_files():
    path = op.join(op.dirname(__file__), 'static/post_images')
    filenames = os.listdir(path)
    used_images_tuple = Post.query.with_entities(Post.post_image).all()
    used_images = [used_image[0] for used_image in used_images_tuple]# tuple을 list로 변환
    used_images.append("escape.jpg")# 기본 이미지는 삭제하면 안됨

    for filename in filenames:
        # print(filename)
        if not filename in used_images:
            os.remove(path + '/' + filename)

    return redirect(url_for('clean_files.index'))

# User Page
@app.route('/')
@app.route('/home')
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts, title='Home', administrator_list=administrator_list)

@app.route('/home/<string:username>')
@login_required
def my_posts(username):
    # posts = Post.query.join(User).filter(User.username==current_user.username).all()
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).all()
    return render_template('home.html', posts=posts, title=username, administrator_list=administrator_list)



@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    save_post_foldername = 'post_images'
    if form.validate_on_submit():
        if form.post_image.data:
            image_file = form.post_image.data
            save_post_objectname = generate_filename(image_file)
            save_image(image_file, save_post_foldername, save_post_objectname)# for local development
            # Post File to AWS S3 using presigned url --------------------------------------
            # Generate a presigned S3 POST URL
            post_to_aws_s3(image_file, save_post_foldername, save_post_objectname)
            #print(image_file.read())

            # ------------------------------------------------------------------------------            
            
            post = Post(title=form.title.data, content=form.content.data, result=form.result.data, author=current_user, post_image=save_post_objectname)
        else:    
            post = Post(title=form.title.data, content=form.content.data, result=form.result.data, author=current_user)
        db.session.add(post)
        db.session.commit()        

        flash('새로운 추억이 생성되었습니다!', 'success')
        return redirect(url_for('home'))
    post_image = url_for('static', filename='post_images/escape.jpg')
    legend = '추억 만들기'
    return render_template('create_post.html', title='Create', form=form, post_image=post_image, legend=legend)

@app.route('/<int:post_id>/update_post', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    selected_post = Post.query.get_or_404(post_id)
    if selected_post.author == current_user:
        form = PostForm()
        save_post_foldername = 'post_images'
        if request.method == 'GET':
            form.title.data = selected_post.title
            form.content.data = selected_post.content
            form.result.data = selected_post.result

        elif form.validate_on_submit():
            if form.post_image.data:
                image_file = form.post_image.data
                save_post_objectname = generate_filename(image_file)
                save_image(image_file, save_post_foldername, save_post_objectname)# for local development                 
                selected_post.post_image = save_post_objectname
        
                selected_post.title = form.title.data
                selected_post.content = form.content.data
                selected_post.result = form.result.data
            db.session.commit()
            flash('추억이 업데이트 되었습니다!', 'success')            
            return redirect(url_for('home'))
    else:
        abort(403)# 403 is "Forbidden" error

    post_image = url_for('static', filename='post_images/'+selected_post.post_image)
    legend = '추억 업데이트'
    return render_template('create_post.html', title='Update', form=form, post_image=post_image, legend=legend)

@app.route('/<int:post_id>/delete_post', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    selected_post = Post.query.get_or_404(post_id)
    if selected_post.author == current_user:
        db.session.delete(selected_post)
        db.session.commit()
        flash('추억이 소멸되었습니다!', 'success')
        return redirect(url_for('home'))
    else:
        abort(403)# 403 is "Forbidden" error

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    save_profile_foldername = 'profile_images'
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if form.profile_image.data:
            image_file = form.profile_image.data
            save_profile_objectname = generate_filename(image_file)
            save_image(image_file, save_profile_foldername, save_profile_objectname)# for local development
  
            user = User(username=form.username.data, email=form.email.data, password=hashed_password, profile_image=save_profile_objectname)
        else:     
            user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다. 로그인을 해주시기 바랍니다.', 'success')
        return redirect(url_for('login'))

    profile_image = url_for('static', filename='profile_images/howwwwwhy.png')
    return render_template('/auth/register.html', title='Register', form=form, profile_image=profile_image)

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('로그인 되었습니다!', 'success')
            next_page = request.args.get('next')
            
            return redirect(next_page) if next_page else redirect(url_for('home'))# Ternary Operator in Python
        else:
            flash('로그인에 실패하였습니다. Username과 Password를 다시 한 번 확인해주세요!', 'error')
    return render_template('/auth/login.html', title='Log in', form=form)

@app.route('/auth/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    save_profile_foldername = 'profile_images'
    if request.method == 'GET':
        form.email.data = current_user.email  

    elif form.validate_on_submit():  
        if form.profile_image.data:
            image_file = form.profile_image.data
            save_profile_objectname = generate_filename(image_file)
            save_image(image_file, save_profile_foldername, save_profile_objectname)# for local development
 
            current_user.profile_image = save_profile_objectname
        current_user.email = form.email.data
        db.session.commit()
        flash('프로필이 업데이트 되었습니다.', 'success')
        return redirect(url_for('account'))     


    profile_image = url_for('static', filename='profile_images/'+current_user.profile_image)
    arrow_image = url_for('static', filename='page_images/green_arrow.png')
    return render_template('account.html', title='Account', form=form, profile_image=profile_image, profile_image_after=profile_image, arrow_image=arrow_image)