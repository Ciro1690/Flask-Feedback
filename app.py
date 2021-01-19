from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///flask-feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route("/")
def homepage():
    return render_template("/home.html")

@app.route("/register", methods=['GET', 'POST'])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username already taken")
            return render_template("register.html", form=form)

        session['username'] = new_user.username
        flash("Created new account", "success")
        return redirect('/')

    return render_template("register.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            flash(f"Welcome {user.first_name}", "success")
            session['username'] = user.username
            return redirect(f'/user/{user.username}')
        else:
            form.username.errors = ['Invalid username/password']
    return render_template('login.html', form=form)

@app.route("/user/<username>")
def user_info(username):
    if 'username' not in session:
        flash("Please log in to view this page", "danger")
        return redirect('/login')
    if session['username'] == username:
        user = User.query.get_or_404(username)
        return render_template("user_info.html", user=user)
    else:
        flash("Invalid username", "danger")
        return redirect("/")

@app.route("/user/<username>/delete", methods=['POST'])
def delete_user(username):
    if 'username' not in session:
        flash("Please log in to view this page", "danger")
        return redirect('/login')
    if session['username'] == username:
        user = User.query.get_or_404(username)
        db.session.delete(user)
        db.session.commit()
        flash("User deleted", "success")
        return redirect("/logout")
    flash("You don't have permission", "danger")
    return redirect("/")

@app.route("/user/<username>/feedback/add", methods=['GET', 'POST'])
def add_feedback(username):
    if 'username' not in session:
        flash("Please login first", "danger")
        return redirect('/')
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title,content=content,username=session['username'])
        db.session.add(new_feedback)
        db.session.commit()
        flash('Feedback added', "success")
        return redirect(f"/user/{username}")
    return render_template("add_feedback.html", form=form)

@app.route("/feedback/<feedback_id>/update", methods=['GET', 'POST'])
def update_feedback(feedback_id):
    if 'username' not in session:
        flash("Please login first", "danger")
        return redirect('/')
    feedback = Feedback.query.filter_by(id=feedback_id).first()
    if not feedback:
        flash("Feedback doesn't exist", "danger")
        return redirect("/")
    form = FeedbackForm(obj=feedback)

    if (session['username'] != feedback.user.username):
        flash("You can only change your own feedback", "danger")
        return redirect('/')

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback updated', "success")
        return redirect(f'/user/{feedback.user.username}')
    return render_template("update_feedback.html", form=form, feedback=feedback)

@app.route("/feedback/<feedback_id>/delete", methods=['POST'])
def delete_feedback(feedback_id):
    if 'username' not in session:
        flash("Please login first", "danger")
        return redirect('/')

    feedback = Feedback.query.get_or_404(feedback_id)
    if (session['username'] != feedback.user.username):
        flash("You can only change your own feedback", "danger")
        return redirect('/')
        
    db.session.delete(feedback)
    db.session.commit()
    flash('Feedback deleted', "success")
    return redirect('/')

@app.route("/logout")
def logout():
    session.pop('username')
    flash('You are now logged out', "success")
    return redirect('/')
