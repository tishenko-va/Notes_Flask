from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from models import db, User, Note
from forms import UserRegisterForm, NoteForm, UserLoginForm
from flask_login import login_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'register'


@app.route('/')
def home():
    return "Добро пожаловать в заметки"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('note_list'))  # Если пользователь уже вошел, перенаправляем на список заметок

    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):  # Проверьте правильность пароля
            login_user(user)
            return redirect(url_for('note_list'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('register'))


@app.route('/notes', methods=['GET'])
@login_required
def note_list():
    current_user_id = current_user.id
    notes_list = Note.query.filter_by(user_id=current_user_id).order_by(Note.created_at.desc()).all()
    return render_template('note_list.html', notes=notes_list)


@app.route('/notes/create', methods=['GET', 'POST'])
@login_required
def note_create():
    form = NoteForm()
    if form.validate_on_submit():
        new_note = Note(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()

        return redirect(url_for('note_list'))

    return render_template('note_form.html', form=form)


@app.route('/notes/update/<int:note_id>', methods=['GET', 'POST'])
@login_required
def note_update(note_id):
    note = Note.query.get_or_404(note_id)
    form = NoteForm(obj=note)

    if form.validate_on_submit():
        note.content = form.content.data
        db.session.commit()
        return redirect(url_for('note_list'))

    return render_template('note_form.html', form=form)


@app.route('/notes/delete/<int:note_id>', methods=['GET', 'POST'])
@login_required
def note_delete(note_id):
    note = Note.query.get_or_404(note_id)

    if request.method == 'POST':
        db.session.delete(note)
        db.session.commit()
        return redirect(url_for('note_list'))

    return render_template('delete.html', note=note)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
