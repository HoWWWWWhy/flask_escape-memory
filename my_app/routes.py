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
from .my_functions import generate_filename, save_image, post_to_aws_s3, get_from_aws_s3, get_all_s3_objects, delete_s3_objects
import secrets

# for Heroku & AWS S3
#import json, boto3
#from botocore.client import Config

#S3_BUCKET = app.config['S3_BUCKET']
#ACCESS_KEY = app.config['S3_KEY']
#SECRET_KEY = app.config['S3_SECRET']

#s3_client = boto3.client('s3',
#    aws_access_key_id=ACCESS_KEY,
#    aws_secret_access_key=SECRET_KEY,
#    config = Config(signature_version = 's3v4')
#)

# 관리자 페이지로 옮기기
#@app.route('/show_s3')
#def show_s3():
#    s3_resource = boto3.resource('s3')
#    my_bucket = s3_resource.Bucket(S3_BUCKET)
#    my_objects = get_from_aws_s3()
#    print(my_objects)
#    bucket_policy = s3_client.get_bucket_policy(Bucket=S3_BUCKET)
#
#    return render_template('view_bucket.html', my_bucket=my_bucket, files=my_objects, bucket_policy=bucket_policy)

# preview.js에서 바로 onchange 이벤트 시 s3에 업로드할 때 요청하는 페이지.
#@app.route('/sign_s3/')
#def sign_s3():
#    file_name = request.args.get('file_name')
#    file_type = request.args.get('file_type')
#
#    presigned_post = s3_client.generate_presigned_post(
#        Bucket = S3_BUCKET,
#        Key = file_name,
#        Fields = {"acl": "public-read", "Content-Type": file_type},
#        Conditions = [
#            {"acl": "public-read"},
#            {"Content-Type": file_type}
#        ],
#        ExpiresIn = 600
#    )
#
#    return json.dumps({
#      'data': presigned_post,
#      'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
#      #'url': 'https://%s.s3.ap-northeast-2.amazonaws.com/%s' % (S3_BUCKET, file_name)
#    })


############################## Admin Page ##############################
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

@app.route('/admin/clean_files/clean_s3_profile_files')
def clean_s3_profile_files():
    profile_foldername = 'profile_images'

    used_images_tuple = User.query.with_entities(User.profile_image).all()
    used_images = [profile_foldername + '/' + used_image[0] for used_image in used_images_tuple]# tuple을 list로 변환
    used_images.append(profile_foldername + '/' + "howwwwwhy.png")# 기본 이미지는 삭제하면 안됨
    #print(used_images)
    s3_profile_objects = get_all_s3_objects(profile_foldername)# s3에서 가져온 리스트
    #print(s3_profile_objects)   

    # 가져온 리스트에서 DB에 없는 파일 삭제, 기본 이미지는 삭제하면 안됨
    unused_objects = list(filter(lambda x: x not in used_images, s3_profile_objects))
    #print(unused_objects)

    if len(unused_objects) > 0:
        is_deleted = delete_s3_objects(unused_objects)

    return redirect(url_for('clean_files.index'))

@app.route('/admin/clean_files/clean_s3_post_files')
def clean_s3_post_files():
    post_foldername = 'post_images'

    used_images_tuple = Post.query.with_entities(Post.post_image).all()
    used_images = [post_foldername + '/' + used_image[0] for used_image in used_images_tuple]# tuple을 list로 변환
    used_images.append(post_foldername + '/' + "escape.jpg")# 기본 이미지는 삭제하면 안됨

    s3_post_objects = get_all_s3_objects(post_foldername)# s3에서 가져온 리스트
    #print(s3_post_objects)
    
    # 가져온 리스트에서 DB에 없는 파일 삭제, 기본 이미지는 삭제하면 안됨
    unused_objects = list(filter(lambda x: x not in used_images, s3_post_objects))
    #print(unused_objects)

    if len(unused_objects) > 0:
        is_deleted = delete_s3_objects(unused_objects)

    return redirect(url_for('clean_files.index'))



############################## User Page ##############################
@app.route('/')
@app.route('/home')
def home():
    post_foldername = 'post_images'
    profile_foldername = 'profile_images'

    # AWS S3에서 가져온 파일리스트들의 url을 DB 저장 순으로 정렬하기
    # 주의: S3에는 그동안 저장된 모든 것들이 있고, DB는 최종 결과만 있음. DB 파일 이름과 일치하는 것 찾기

    posts = Post.query.all()
    s3_post_key_list = [post_foldername + '/' + post.post_image for post in posts]
    s3_profile_key_list = [profile_foldername + '/' + post.author.profile_image for post in posts]
    #print(s3_post_key_list)
    #print(s3_profile_key_list)

    s3_post_objects = get_from_aws_s3(s3_post_key_list)
    s3_profile_objects = get_from_aws_s3(s3_profile_key_list)
    #print(s3_profile_objects)
    
    # generator expression
    s3_post_url_list = [s3_post_object['presigned_url'] for s3_post_object in s3_post_objects]
    s3_profile_url_list = [s3_profile_object['presigned_url'] for s3_profile_object in s3_profile_objects]
    #print(s3_profile_url_list)

    # 유저 로그인 시 플로팅메뉴 사진 url 전달
    s3_current_user_profile_url = ""
    if current_user.is_authenticated:
        s3_current_user_profile_object = get_from_aws_s3([profile_foldername + '/' + current_user.profile_image])
        s3_current_user_profile_url = s3_current_user_profile_object[0]['presigned_url']
        #print(s3_current_user_profile_url)

    return render_template('home.html', posts=posts, s3_posts=s3_post_url_list, s3_profiles=s3_profile_url_list,
                            title='Home', administrator_list=administrator_list, s3_current_user=s3_current_user_profile_url)

@app.route('/home/<string:username>')
@login_required
def my_posts(username):
    post_foldername = 'post_images'
    profile_foldername = 'profile_images'

    # posts = Post.query.join(User).filter(User.username==current_user.username).all()
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).all()

    s3_post_key_list = [post_foldername + '/' + post.post_image for post in posts]
    s3_profile_key_list = [profile_foldername + '/' + post.author.profile_image for post in posts]

    s3_post_objects = get_from_aws_s3(s3_post_key_list)
    s3_profile_objects = get_from_aws_s3(s3_profile_key_list)

    s3_post_url_list = [s3_post_object['presigned_url'] for s3_post_object in s3_post_objects]
    s3_profile_url_list = [s3_profile_object['presigned_url'] for s3_profile_object in s3_profile_objects]

    # 유저 로그인 시 플로팅메뉴 사진 url 전달
    s3_current_user_profile_url = ""
    if current_user.is_authenticated:
        s3_current_user_profile_object = get_from_aws_s3([profile_foldername + '/' + current_user.profile_image])
        s3_current_user_profile_url = s3_current_user_profile_object[0]['presigned_url']

    return render_template('home.html', posts=posts, s3_posts=s3_post_url_list, s3_profiles=s3_profile_url_list,
                            title=username, administrator_list=administrator_list, s3_current_user=s3_current_user_profile_url)


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

    #post_image = url_for('static', filename=save_post_foldername + '/' + 'escape.jpg')# local
    s3_post_object = get_from_aws_s3([save_post_foldername + '/' + 'escape.jpg'])
    s3_post_url = s3_post_object[0]['presigned_url']

    legend = '추억 만들기'
    return render_template('create_post.html', title='Create', form=form, post_image=s3_post_url, legend=legend)# aws s3
    #return render_template('create_post.html', title='Create', form=form, post_image=post_image, legend=legend)# local

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
                post_to_aws_s3(image_file, save_post_foldername, save_post_objectname)

                selected_post.post_image = save_post_objectname

            selected_post.title = form.title.data
            selected_post.content = form.content.data
            selected_post.result = form.result.data
            db.session.commit()
            flash('추억이 업데이트 되었습니다!', 'success')            
            return redirect(url_for('home'))
    else:
        abort(403)# 403 is "Forbidden" error

    #post_image = url_for('static', filename=save_post_foldername + '/' + selected_post.post_image)# local
    s3_post_object = get_from_aws_s3([save_post_foldername + '/' + selected_post.post_image])
    s3_post_url = s3_post_object[0]['presigned_url']
    
    legend = '추억 업데이트'
    return render_template('create_post.html', title='Update', form=form, post_image=s3_post_url, legend=legend)# aws s3
    #return render_template('create_post.html', title='Update', form=form, post_image=post_image, legend=legend)# local

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
            post_to_aws_s3(image_file, save_profile_foldername, save_profile_objectname)

            user = User(username=form.username.data, email=form.email.data, password=hashed_password, profile_image=save_profile_objectname)
        else:     
            user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다. 로그인을 해주시기 바랍니다.', 'success')
        return redirect(url_for('login'))

    #profile_image = url_for('static', filename=save_profile_foldername + '/' + 'howwwwwhy.png')# local
    s3_profile_object = get_from_aws_s3([save_profile_foldername + '/' + 'howwwwwhy.png'])
    s3_profile_url = s3_profile_object[0]['presigned_url']    
    return render_template('/auth/register.html', title='Register', form=form, profile_image=s3_profile_url)# aws s3
    #return render_template('/auth/register.html', title='Register', form=form, profile_image=profile_image)# local

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
            post_to_aws_s3(image_file, save_profile_foldername, save_profile_objectname)

            current_user.profile_image = save_profile_objectname
        current_user.email = form.email.data
        db.session.commit()
        flash('프로필이 업데이트 되었습니다.', 'success')
        return redirect(url_for('account'))     

    #profile_image = url_for('static', filename=save_profile_foldername + '/' + current_user.profile_image)# local
    s3_profile_object = get_from_aws_s3([save_profile_foldername + '/' + current_user.profile_image])
    s3_profile_url = s3_profile_object[0]['presigned_url']

    arrow_image = url_for('static', filename='page_images/green_arrow.png')
    return render_template('account.html', title='Account', form=form, profile_image=s3_profile_url, profile_image_after=s3_profile_url, arrow_image=arrow_image)# aws s3
    #return render_template('account.html', title='Account', form=form, profile_image=profile_image, profile_image_after=profile_image, arrow_image=arrow_image)# local