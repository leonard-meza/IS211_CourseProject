import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'


def get_db_connection():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute(
        'select posts.id, posts.title, posts.content, posts.created, '
        'categories.name AS category_name, posts.category_id '
        'from posts JOIN categories ON posts.category_id = categories.id '
        'where posts.published = 1 ORDER BY posts.created DESC').fetchall()

    conn.close()
    return render_template('index.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """login page authenticating w/ user table """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash('all the fields are required')
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    'insert into users (username, password) values (?, ?)',
                    (username, password)
                )
                conn.commit()
                flash('registered, thank you for registering')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('username not available please try again')
            finally:
                conn.close()
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    """showing posts belonging to user with edit/delete/un-publish """
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute(
        'select posts.id, posts.title, posts.published, posts.category_id, '
        'categories.name as category_name '
        'from posts join categories on posts.category_id = categories.id '
        'where posts.user_id = ?', (session['user_id'],)).fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('dashboard.html', posts=posts, categories=categories)


@app.route('/create', methods=['POST'])
def create():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    title = request.form['title']
    content = request.form['content']
    category_id = request.form['category_id']
    if not title or not content:
        flash('Title and Content are required!')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    conn.execute(
        'insert into posts (title, content, user_id, category_id) VALUES (?, ?, ?, ?)',
        (title, content, session['user_id'], category_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    """Edit existing post--- only logged in can edit """
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    if post is None or post['user_id'] != session['user_id']:
        conn.close()
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category_id']
        if not title or not content:
            flash('Title and Content are required!')
        else:
            conn.execute(
                'update posts set title = ?, content = ?, category_id = ? where id = ?',
                (title, content, category_id, post_id))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit.html', post=post, categories=categories)


@app.route('/delete/<int:post_id>')
def delete(post_id):
    """delete a post. Only logged in can delete """
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and post['user_id'] == session['user_id']:
        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/unpublish/<int:post_id>')
def unpublish(post_id):
    """un-publish a post hiding from public index """
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and post['user_id'] == session['user_id']:
        conn.execute('update posts set published = 0 where id = ?', (post_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/publish/<int:post_id>')
def publish(post_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and post['user_id'] == session['user_id']:
        conn.execute('UPDATE posts SET published = 1 WHERE id = ?', (post_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/add_category', methods=['POST'])
def add_category():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    name = request.form['name']
    if name:
        conn = get_db_connection()
        conn.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
    return redirect(url_for('dashboard'))


@app.route('/categories')
def categories():
    conn = get_db_connection()
    cats = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('categories.html', categories=cats)


@app.route('/category/<int:cat_id>')
def category(cat_id):
    conn = get_db_connection()
    category = conn.execute('SELECT * FROM categories WHERE id = ?', (cat_id,)).fetchone()
    posts = conn.execute(
        'select posts.id, posts.title, posts.content, posts.created '
        'from posts where category_id = ? and published = 1 order by created DESC',
        (cat_id,)).fetchall()
    conn.close()
    if category is None:
        abort(404)
    return render_template('category.html', posts=posts, category_name=category['name'])


@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db_connection()
    post = conn.execute(
        'select posts.id, posts.title, posts.content, posts.created, '
        'posts.published, posts.category_id, categories.name AS category_name '
        'from posts join categories on posts.category_id = categories.id '
        'where posts.id = ?', (post_id,)
    ).fetchone()
    conn.close()
    if post is None or post['published'] == 0:
        abort(404)
    return render_template('post.html', post=post)


if __name__ == '__main__':
    app.run(debug=True)
