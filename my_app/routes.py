from flask import render_template, url_for, flash, redirect, request, abort
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from .db_models import User, Post
from my_app import app, db, bcrypt, admin
from flask_login import login_user, current_user, logout_user, login_required
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
import secrets
import os
# from PIL import Image
from flask_admin.contrib.fileadmin import FileAdmin
import os.path as op

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

path_project = op.join(op.dirname(__file__), '/HoWWWWWhy/flask_escape-memory/my_app')
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
    if form.validate_on_submit():
        if form.post_image.data:
            post_image = save_image(form.post_image.data, 'post_images')   
            post = Post(title=form.title.data, content=form.content.data, result=form.result.data, author=current_user, post_image=post_image)
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

        if request.method == 'GET':
            form.title.data = selected_post.title
            form.content.data = selected_post.content
            form.result.data = selected_post.result

        elif form.validate_on_submit():
            if form.post_image.data:
                post_image = save_image(form.post_image.data, 'post_images')   
                selected_post.post_image = post_image
        
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


def save_image(form_image, save_foldername):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_filename = random_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/'+save_foldername, image_filename)

    # output_size = (200, 200)
    # im = Image.open(form_image)
    # im.thumbnail(output_size)
    # im.save(image_path)

    form_image.save(image_path)

    return image_filename

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if form.profile_image.data:
            profile_image = save_image(form.profile_image.data, 'profile_images')   
            user = User(username=form.username.data, email=form.email.data, password=hashed_password, profile_image=profile_image)
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
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            
            return redirect(next_page) if next_page else redirect(url_for('home'))# Ternary Operator in Python
        else:
            flash('Login Unsuccessful. Please check again!', 'error')
    return render_template('/auth/login.html', title='Log in', form=form)

@app.route('/auth/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if request.method == 'GET':
        form.email.data = current_user.email  

    elif form.validate_on_submit():  
        if form.profile_image.data:
            profile_image = save_image(form.profile_image.data, 'profile_images')   
            current_user.profile_image = profile_image
        current_user.email = form.email.data
        db.session.commit()
        flash('프로필이 업데이트 되었습니다.', 'success')
        return redirect(url_for('account'))     


    profile_image = url_for('static', filename='profile_images/'+current_user.profile_image)
    arrow_image = url_for('static', filename='page_images/green_arrow.png')
    return render_template('account.html', title='Account', form=form, profile_image=profile_image, profile_image_after=profile_image, arrow_image=arrow_image)