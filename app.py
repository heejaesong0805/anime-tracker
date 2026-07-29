from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from flask_migrate import Migrate



load_dotenv() # Loads the .env file

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY')

# Configure the SQLite database, relative to the app instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database tool
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'login' # Redirects users here if they aren't logged in
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# New User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # This establishes the relationship to the Anime table
    animes = db.relationship('Anime', backref='owner', lazy=True)

# Updated Anime Model
class Anime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # The 'nametag' linking this anime to a specific user's ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, name, user_id) -> None:
        self.name = name
        self.user_id = user_id
        

# Create the database file and tables if they don't exist yet
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        new_anime_name = request.form.get('anime_name')
        if new_anime_name:
            # Create a new Anime object and save it to the database
            new_anime = Anime(name=new_anime_name, user_id=current_user.id)
            db.session.add(new_anime)
            db.session.commit()
            
        return redirect(url_for('home'))
    
    # Query all animes from the database
    return render_template('index.html', animes=current_user.animes)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 1. Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # In a production app, you'd use a UI error message here
            return "That username is already taken. Please try another one."

        # 2. Encrypt the password using Werkzeug
        hashed_password = generate_password_hash(password)

        # 3. Create the new user and save them to the database
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # 4. Redirect them to the login page so they can sign in
        return redirect(url_for('login'))

    # If it's a GET request, just show the HTML page
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 1. Look up the user by their username
        user = User.query.filter_by(username=username).first()

        # 2. Check if the user exists AND the password is correct
        if user and check_password_hash(user.password_hash, password):
            # Log the user in and remember their session
            login_user(user)
            # Redirect them to their personal anime tracker
            return redirect(url_for('home'))
        else:
            return "Invalid username or password. Please try again."

    # If it's a GET request, just show the HTML page
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    # Clears the user's session
    logout_user()
    # Sends them back to the login page
    return redirect(url_for('login'))


@app.route('/delete/<int:id>')
def delete(id):
    # Find the specific anime by its database ID
    anime_to_delete = db.session.get(Anime, id)
    
    # If it exists, delete it and save the changes
    if anime_to_delete:
        db.session.delete(anime_to_delete)
        db.session.commit()
        
    # Send the user back to the home page
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)