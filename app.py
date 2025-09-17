from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from uuid import uuid4
from supabase import create_client, Client
import os
from config import Config
from functools import wraps  # for proper decorator wrapping

# Supabase configuration
supabase_url: str = Config.SUPABASE_URL
supabase_key: str = Config.SUPABASE_KEY
supabase: Client = create_client(supabase_url, supabase_key)

def fetch_posts():
    resources_response = supabase.table('resources').select("*").execute()
    resources = resources_response.data

    posts = []
    for resource in resources:
        status_response = (
            supabase.table('status_updates')
            .select("*")
            .eq('resource_id', resource['id'])
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        status = status_response.data[0] if status_response.data else None

        # Get upvote count
        upvotes_response = (
            supabase.table('upvotes')
            .select('id', count='exact')
            .eq('resource_id', resource['id'])
            .execute()
        )
        upvotes_count = upvotes_response.count if hasattr(upvotes_response, 'count') else len(upvotes_response.data)

        post = {
            'id': resource['id'],
            'title': resource['name'],
            'image_url': resource.get('image_url'),
            'description': status['status_message'] if status else '',
            'upvotes': upvotes_count,
            'comments': 0,  # Placeholder if comments table is added later
            'crowd': status['crowd_level'] if status else '',
            'chips': status['chips_available'] if status else '',
            'queue': status['queue_length'] if status else ''
        }
        posts.append(post)

    posts.sort(key=lambda x: x['upvotes'], reverse=True)
    return posts


app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']


@app.route('/upvote', methods=['POST'])
def upvote():
    if 'username' not in session:
        return jsonify({'error': 'Login required'}), 401

    resource_id = request.json.get('resource_id')
    user_id = session.get('user_id')

    # Prevent double upvote
    result = (
        supabase.table('upvotes')
        .select('*')
        .eq('resource_id', resource_id)
        .eq('user_id', user_id)
        .execute()
    )
    if result.data:
        return jsonify({'error': 'Already upvoted'}), 409

    supabase.table('upvotes').insert({
        'id': str(uuid4()),
        'resource_id': resource_id,
        'user_id': user_id
    }).execute()

    # Return new upvote count
    count = (
        supabase.table('upvotes')
        .select('id', count='exact')
        .eq('resource_id', resource_id)
        .execute()
        .count
    )
    return jsonify({'success': True, 'upvotes': count})


# --------- Decorators ---------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# --------- Routes ---------
@app.route('/')
def index():
    posts = fetch_posts()
    return render_template('index.html', posts=posts, username=session.get('username'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            user = supabase.auth.sign_in_with_password(
                {"email": username, "password": password}
            )
            if user and hasattr(user, "user") and user.user:
                session['username'] = username
                session['is_admin'] = False
                session['user_id'] = user.user.id
                return redirect(url_for('profile'))
            else:
                return render_template('login.html', error="Invalid credentials")
        except Exception as e:
            return render_template('login.html', error=str(e))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            user = supabase.auth.sign_up({"email": username, "password": password})
            if user and hasattr(user, "user") and user.user:
                session['username'] = username
                session['user_id'] = user.user.id
                return redirect(url_for('profile'))
            else:
                return render_template('register.html', error="Registration failed")
        except Exception as e:
            return render_template('register.html', error=str(e))
    return render_template('register.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=session['username'])


@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/update_post/<post_id>', methods=['POST'])
@login_required
def update_post(post_id):
    description = request.form['description']
    crowd = request.form['crowd']
    chips = request.form['chips']
    queue = request.form['queue']

    # Check if a status update exists
    status_response = supabase.table('status_updates').select("*").eq('resource_id', post_id).execute()
    status = status_response.data

    if status:
        supabase.table('status_updates').update({
            'crowd_level': crowd,
            'chips_available': chips,
            'queue_length': queue,
            'status_message': description
        }).eq('resource_id', post_id).execute()
    else:
        supabase.table('status_updates').insert({
            'id': str(uuid4()),
            'resource_id': post_id,
            'crowd_level': crowd,
            'chips_available': chips,
            'queue_length': queue,
            'status_message': description
        }).execute()

    return redirect(url_for('index'))


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        crowd = request.form['crowd']
        chips = request.form['chips']
        queue = request.form['queue']

        # Insert new resource
        resource_id = str(uuid4())
        supabase.table('resources').insert({
            'id': resource_id,
            'name': title,
        }).execute()

        # Insert initial status update
        supabase.table('status_updates').insert({
            'id': str(uuid4()),
            'resource_id': resource_id,
            'status_message': description,
            'crowd_level': crowd,
            'chips_available': chips,
            'queue_length': queue,
        }).execute()

        return redirect(url_for('index'))
    return render_template('create_post.html')


# --------- Run ---------
if __name__ == '__main__':
    # for production, use waitress. For dev, keep debug=True
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)
    app.run(debug=True)
