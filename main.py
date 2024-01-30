from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from extensions import db  # Import db from extensions
from forms import PostForm, SubscribeForm, ContactForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import session
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import BadRequest
import re
from flask_mail import Message, Mail
from flask_migrate import Migrate  # Import Flask-Migrate
import cv2
import numpy as npfrom flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from extensions import db  # Import db from extensions
from forms import PostForm, SubscribeForm, ContactForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import session
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import BadRequest
import re
from flask_mail import Message, Mail
from flask_migrate import Migrate  # Import Flask-Migrate
import cv2
import numpy as np
import sys

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


# Custom slugify function based on the re module
def slugify(text):
    # Add print statements for debugging
    print(f"Input text: {text}")
    # Remove special characters and spaces, and convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9]', ' ', text).strip().lower()
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    return text

# Function to update slugs for existing posts
def update_existing_post_slugs():
    print("Updating slugs for existing posts...")  # Add this line for debugging
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

# Create Post Route
@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    form = PostForm()
    if request.method == 'POST':
        print("Post request received")  # Debugging

    if form.validate_on_submit():
        print("Form is valid")  # Debugging
        try:
            post_title = form.title.data
            post_content = form.content.data
            post_author = 'Maki'  # Placeholder author

            # Generate the slug from the post title
            slug = slugify(post_title)  # Replace with your custom slugify function

            # Handle Image Upload
            file = form.post_image.data
            post_image_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                post_image_path = os.path.join('images/blogimages', filename)

            new_post = BlogPost(title=post_title, content=post_content, slug=slug, author=post_author)
            db.session.add(new_post)
            db.session.commit()
            print("New post added:", new_post)  # Debugging
            return redirect(url_for('index'))
        except Exception as e:
            print("Failed to add post:", e)
    else:
        print("Form validation failed")  # Debugging
        print(form.errors)  # Print form errors if validation fails

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

# Other functions

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: csrf.generate_csrf())

# Helper function to check allowed file types
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Crop Hero Video
def main():
    # Open the video
    video_path = '../static/video/laptop_animenew.mp4'
    cap = cv2.VideoCapture(video_path)

    # Check if video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # Read video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, fps, (frame_width, frame_height))

    # Process video frames here in the next step

    # Release everything when the job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        main(video_path)
    else:
        print("Please provide the path to the video file.")
        # Optionally, you can set a default path or exit the script
        # video_path = 'default/path/to/video.mp4'
        # main(video_path)
    
    update_existing_post_slugs()
    print("Updated slugs for existing posts.")

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
import sys

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

# Create Post Route
@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    form = PostForm()
    if request.method == 'POST':
        print("Post request received")  # Debugging

    if form.validate_on_submit():
        print("Form is valid")  # Debugging
        try:
            post_title = form.title.data
            post_content = form.content.data
            post_author = 'Maki'  # Placeholder author

            # Generate the slug from the post title
            slug = slugify(post_title)  # Replace with your custom slugify function

            # Handle Image Upload
            file = form.post_image.data
            post_image_path = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                post_image_path = os.path.join('images/blogimages', filename)

            new_post = BlogPost(title=post_title, content=post_content, slug=slug, author=post_author)
            db.session.add(new_post)
            db.session.commit()
            print("New post added:", new_post)  # Debugging
            return redirect(url_for('index'))
        except Exception as e:
            print("Failed to add post:", e)
    else:
        print("Form validation failed")  # Debugging
        print(form.errors)  # Print form errors if validation fails

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

# Other functions

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: csrf.generate_csrf())

# Helper function to check allowed file types
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Crop Hero Video
def main():
    # Open the video
    video_path = '../static/video/laptop_animenew.mp4'
    cap = cv2.VideoCapture(video_path)

    # Check if video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # Read video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, fps, (frame_width, frame_height))

    # Process video frames here in the next step

    # Release everything when the job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        main(video_path)
    else:
        print("Please provide the path to the video file.")
        # Optionally, you can set a default path or exit the script
        # video_path = 'default/path/to/video.mp4'
        # main(video_path)
    
    update_existing_post_slugs()
    print("Updated slugs for existing posts.")

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
