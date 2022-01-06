import json

from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, Markup, get_template_attribute, session, jsonify, send_from_directory
from flask_login import current_user, login_user, login_required, logout_user
from photo_app import app

from photo_app.models import User, Photo, Post, FavoritePosts, db_session, db, load_user
from manage import factory_setup, factory_teardown
from pony.orm import select
from dateutil.relativedelta import relativedelta
from werkzeug import secure_filename
import os, base64

app.config['UPLOAD_FOLDER']='logs'


@app.route('/signup', methods=['GET', 'POST'])
@db_session
def signup():
    if request.method == 'GET':
        return render_template('signup.html', title='Sign Up')
    elif request.method == 'POST':
        
        if request.form['password'] == request.form['confirm_password']:
            u = select(user for user in User if user.email==request.form['email'] or user.username==request.form['username'])
            if u.count() != 0:
                flash('Email or username are already in use.', 'red')
                return redirect(url_for('signup'))
            else:
                user = User(username=request.form['username'],
                            email=request.form['email'])
                user.set_password(request.form['password'])
                user = User.get(email=request.form['email'])
          
            login_user(user, force=True)
            flash('Welcome to photo_app! Your account was successfully created.', 'green')
            data = {'email':request.form['email'], 'password':request.form['password']}

            return redirect(url_for('login'), code=307)


        else:
            flash('The passwords do not match. Please try again.', 'red')
            return redirect(url_for('signup'))


@app.route('/login', methods=['GET', 'POST'])
@db_session
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('onboarding'))
        else:
            return render_template('login.html', title='Login')
    elif request.method == 'POST':
        password = request.form['password']
        if '@' in request.form['email']:
            user = User.get(email=request.form['email'])
        else:
            user = User.get(username=request.form['email'])

        if user is None:
            flash(Markup(
                'There\'s no account associated with this email address.'
                '<a href="/signup" style="color:white"><br>Sign up now.</a>'))
            return redirect(url_for('login'))
        elif not user.check_password(password):
            flash('Oops! Wrong credentials. Please try again.')
            return redirect(url_for('login'))
        else:
            token = jwt.encode({
            'public_id': user.public_id,
            'exp' : datetime.utcnow() + timedelta(minutes = 30)
        }, app.config['SECRET_KEY'])
            login_user(user, force=True)
          
            redirect_url = request.args.get('next')
     
            return redirect(redirect_url or url_for('onboarding'))


@app.route('/logout')
@db_session
@login_required
@token_required
def logout():
    Paths.remove_paths(current_user)
    logout_user()
    return redirect(url_for('index'))


# get the profile page / update profile 
@app.route('/profile', methods=['GET', 'POST'])
@db_session
@login_required
def profile():
    if request.method == 'GET':
        return render_template('profile.html')
    else:
        current_user.set_data([request.form['username'],
                                request.form['email'],
                                request.form['password'],
                               request.form['current_location']])

    return redirect(url_for('profile'))


@app.route('/home', methods=['GET', 'POST'])
@db_session
@login_required
@token_required
def home():
    if request.method == 'GET':
        keyword = request.args.get('keyword', default='all')

        # browse all images
        if keyword == 'all':
            images = Image.select()
        else:
            # search images by key phrases of their name or tags
            images = Image.select(image for image in Image if  keyword in [image.title] or keyword in image.tags)

        return render_template('home.html', images=images)
    else:
        # filter images; let us assume the available categories are nature and buildings
        if 'nature' in request.form:
            images = select(image for image in Image if image.category == 'nature')
        elif 'buildings':
            images = select(image for image in Image if image.category == 'buildings')
        return render_template('home.html', images=images)

    # bookmark images as favorites
    elif request.method == 'POST':
        current_user.set_favorite_post(post)
        return render_template('home.html', images=images)

# browse the favorite posts
@app.route('/bookmarks')
@db_session
@login_required
@token_required
def bookmarks():
    images = select(image for image in Image if current_user.id == FavoritePosts.owner)

#begin image uploading
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@login_required
@token_required
def upload_file():
	if request.method == 'POST':
		space = ''
		imgfile = request.files['image']
		title = request.form.get('title')
		tags = request.form.get('tags')
		#tag = tags.split(' ').strip('#')
		tag = [x.strip('#') for x in tags.split(' ')]
		if space in tag:
			tag.remove('')

		image_data = base64.standard_b64encode(imgfile.read())
		post = Post(title=title, category=category, image=image, tags=tag, owner=current_user.id)
        post.flush()
        return render_template('home.html')

# download images
@app.route('/home/<path:filename>', methods=['GET', 'POST'])
@login_required
@token_required
def download(filename):
    print(app.root_path)
    full_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    print(full_path)
    return send_from_directory(full_path, filename)

