from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from extensions import db  # Import db from extensions
from forms import PostForm, SubscribeForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import session
from flask import jsonify
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import BadRequest
import re
from flask_migrate import Migrate  # Import Flask-Migrate

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

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


# Routes
@app.route('/')
def index():
    form = SubscribeForm()  # Create an instance of the SubscribeForm
    return render_template('index.html', form=form)



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        # Handling the image upload
        file = request.files['post_image']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join('../static/images/blogimages/', filename))

            # Create new BlogPost instance
            post = BlogPost(title=form.title.data, content=form.content.data, post_image=filename)
            db.session.add(post)
            db.session.commit()
        
        return redirect(url_for('index'))

    return render_template('create_post.html', form=form)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    form = PostForm()
    if form.validate_on_submit():
        # Logic to update the post goes here
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('edit_post.html', form=form, post_id=post_id)

@app.route('/view_post/<int:post_id>')
def view_post(post_id):
    # Logic to fetch and display the post goes here
    return render_template('view_post.html', post_id=post_id)

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


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: csrf.generate_csrf())


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
