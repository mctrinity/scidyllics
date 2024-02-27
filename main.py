import json
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from extensions import db  # Import db from extensions
from forms import PostForm, SubscribeForm, ContactForm, WeatherForm, BillboardForm, RegistrationForm, LoginForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import session
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import BadRequest
import re
from flask_mail import Message, Mail
from flask_migrate import Migrate  # Import Flask-Migrate
from weather_data_weatherstack import get_current_weather
import subprocess
from spotify import create_spotify_playlist
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Directory for uploaded images
UPLOAD_FOLDER = 'static/images/blogimages/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mail = Mail(app)

csrf = CSRFProtect(app)

db.init_app(app)  # Initialize db with app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Migrate after the db has been initialized with app
migrate = Migrate(app, db)


# Import models here, after db has been initialized with app
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    post_image = db.Column(db.String(255))  # Assuming image path will be stored
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    comments = db.relationship('Comment', backref='blog_post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    # If you want to link comments to users, add a user_id column here

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_subscribed = db.Column(db.DateTime, default=datetime.utcnow)

# class User(db.Model):
class User(UserMixin, db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # password_hash = db.Column(db.String(128))
    # password_hash = db.Column(db.String(256))
    password_hash = db.Column(db.String(512)) 

    def is_admin(self):
        return self.id == 1  # or other logic to determine admin status

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

# Helper function to check allowed file types
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom slugify function based on the re module
def slugify(text):
    # Remove special characters and spaces, and convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9]', ' ', text).strip().lower()
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    return text

# Function to update slugs for existing posts
def update_existing_post_slugs():
    with app.app_context():
        # Fetch all existing blog posts
        existing_posts = BlogPost.query.all()

        for post in existing_posts:
            # Generate a new slug using the custom slugify function
            new_slug = slugify(post.title)

            # Update the post's slug
            post.slug = new_slug

        # Commit the changes to the database
        db.session.commit()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Routes
@app.route('/')
def index():
    # Create an instance of the SubscribeForm for rendering the form
    form = SubscribeForm()

    # Fetch the latest two posts
    latest_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(2).all()

    # Fetch all posts
    all_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()

    # Replace backslashes in image paths for both latest and all posts
    for post in latest_posts + all_posts:
        if post.post_image:
            post.post_image = post.post_image.replace('\\', '/')

    # Render the index.html template with the necessary data
    return render_template('index.html', form=form, latest_posts=latest_posts, all_posts=all_posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

# Send Mail Function
def send_email(name, user_email, message):
    msg = Message('Sci-Dyllics Message',
                  sender=app.config['MAIL_USERNAME'],  # Use your own email as the sender
                  recipients=[app.config['MAIL_USERNAME']])  # Your email as the recipient
    msg.body = f"Name: {name}\nEmail: {user_email}\nMessage: {message}"
    msg.reply_to = user_email  # Set the user's email as the reply-to address

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(e)  # For debugging purposes
        return False

# Contact Route
from flask import jsonify
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            name = form.name.data
            email = form.email.data
            message = form.message.data

            if send_email(name, email, message):
                return jsonify({'status': 'success', 'message': 'Your message has been sent successfully!'})
            else:
                return jsonify({'status': 'error', 'message': 'An error occurred while sending your message. Please try again later.'})
    
    return render_template('contact.html', form=form)

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You are now registered and can log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Create Post Route
@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    form = PostForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            post_title = form.title.data
            post_content = form.content.data
            post_author = 'Maki'  # Placeholder author

            # Generate the slug from the post title
            slug = slugify(post_title)

            # Handle Image Upload
            file = form.post_image.data
            post_image_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                post_image_path = os.path.join('images/blogimages', filename)

            new_post = BlogPost(
                title=post_title,
                content=post_content,
                slug=slug,  # Set the slug here
                author=post_author,
                post_image=post_image_path
            )

            db.session.add(new_post)
            db.session.commit()
            
            # Redirect to the view_post page for the newly created post
            return redirect(url_for('view_post', slug=slug))
        except Exception as e:
            print("Failed to add post:", e)

    return render_template('create_post.html', form=form)


# Edit Post Route
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = PostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data

        # Generate the slug from the post title
        post.slug = slugify(post.title)  # Replace with your custom slugify function

        # Handle Image Upload
        if 'post_image' in request.files:
            file = request.files['post_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post.post_image = os.path.join('images/blogimages', filename)

        db.session.commit()
        return redirect(url_for('view_post', slug=post.slug))

    return render_template('edit_post.html', form=form, post_id=post_id, post=post)

# View Post Route
@app.route('/post/<string:slug>')
def view_post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    # Replace backslashes with forward slashes in the image path
    if post.post_image:
        post.post_image = post.post_image.replace('\\', '/')
    return render_template('view_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if not current_user.is_authenticated or current_user.id != 1:
        abort(403)  # Forbidden access if not admin

    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post has been deleted successfully.', 'success')
    # return redirect(url_for('gallery'))
    return redirect(url_for('index')) 


# Subscribe Route
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email')

    # Email validation pattern
    email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")

    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required.'}), 400

    if not email_pattern.match(email):
        return jsonify({'status': 'error', 'message': 'Invalid email format.'}), 400

    existing_subscriber = Subscriber.query.filter_by(email=email).first()
    if existing_subscriber:
        return jsonify({'status': 'error', 'message': 'Email already subscribed!'}), 409

    try:
        new_subscriber = Subscriber(email=email)
        db.session.add(new_subscriber)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Subscription successful!'})
    except Exception as e:
        db.session.rollback()  # Rollback in case of any exception
        print(e)  # For debugging purposes, log the exception
        return jsonify({'status': 'error', 'message': 'An error occurred. Please try again later.'}), 500

# Function to read city data from the JSON file
def read_city_data():
    city_data = []

    with open('static\data\cities.json', 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        for entry in data:
            city_data.append(entry['city'])

    return city_data

# Route for the "What's Up?" page
# Modify the 'whatsup' route to handle only weather information
@app.route('/whatsup', methods=['GET', 'POST'])
def whatsup():
    cities = read_city_data()
    weather_form = WeatherForm()  # Create an instance of the WeatherForm class
    billboard_form = BillboardForm()  # Create an instance of the BillboardForm class

    if request.method == 'POST':
        if weather_form.validate_on_submit():
            city = weather_form.city.data  # Get the inputted city from the form

            # Call your weather data function here, passing the inputted city
            weather_data = get_current_weather(city)  # Replace with your actual function and API call

            return render_template('whatsup.html', cities=cities, weather_data=weather_data, weather_form=weather_form, billboard_form=billboard_form)

    return render_template('whatsup.html', cities=cities, weather_form=weather_form, billboard_form=billboard_form)


# Define the create_playlist route
# Route to create a Spotify playlist
@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    error_message = None
    success_message = None
    playlist_url = None

    if request.method == 'POST':
        date = request.form.get('date')

        # Call the create_spotify_playlist function to create the playlist
        playlist_url = create_spotify_playlist(date)

        if playlist_url:
            success_message = "Playlist created successfully!"
        else:
            error_message = "Error creating playlist. Please check your input and try again."

    return render_template('create_playlist.html', success_message=success_message, error_message=error_message, playlist_url=playlist_url)


if __name__ == '__main__':
    app.run(debug=True)

# Other functions

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: csrf.generate_csrf())



if __name__ == "__main__":
    update_existing_post_slugs()
    print("Updated slugs for existing posts.")

    # Run the Flask application
    app.run(debug=True)
