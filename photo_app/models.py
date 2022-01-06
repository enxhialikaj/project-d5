import os
from decimal import Decimal
from pony.orm import Database, Required, Optional, PrimaryKey, Set, db_session, StrArray
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from photo_app import login
import datetime

db = Database()

class User(UserMixin, db.Entity):
    _table_ = 'users'
    id = PrimaryKey(int, auto=True)
    email = Required(str, unique=True)
    username = Required(str, unique=True)
    password_hash = Optional(str)
    posts = Set("Post", reverse="owner")
    current_location = Optional(str)
    favorite_posts = Set("FavoritePosts", reverse="owner")

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @db_session
    def set_data(self, data):
        self.username = data[0]
        self.email = data[1]
        self.password = data[2]
        self.current_location[3]

    @db_session
    def set_favorite_post(self, post):
        self.post = post

    # decorator for verifying the JWT
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            # jwt is passed in the request header
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
            # return 401 if token is not passed
            if not token:
                return jsonify({'message' : 'Token is missing !!'}), 401
    
            try:
                # decoding the payload to fetch the stored details
                data = jwt.decode(token, app.config['SECRET_KEY'])
                current_user = User.query\
                    .filter_by(public_id = data['public_id'])\
                    .first()
            except:
                return jsonify({
                    'message' : 'Token is invalid !!'
                }), 401
            # returns the current logged in users contex to the routes
            return  f(current_user, *args, **kwargs)
    
        return decorated

class Post(db.Entity):
    _table_ = 'posts'
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    category = Required(str, unique=True)
    image = Required(buffer)
    owner = Required("User", reverse="posts")
    tags = Optional(StrArray)

class FavoritePosts(db.Entity):
    _table_ = 'favorite_posts'
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    category = Required(str, unique=True)
    image = Required(buffer)
    owner = Optional("User", reverse="favorite_posts")

@login.user_loader
@db_session
def load_user(id):
    try:
        return User.get(id=int(id))
    except:
        return


if os.environ['FLASK_ENV'] == 'testing':
    db.bind(provider='sqlite', filename='../test.db', create_db=True)
    db.generate_mapping(create_tables=True)

else:
    db.bind(provider='sqlite', filename='../dev.db', create_db=True)
    db.generate_mapping(create_tables=True)
