from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
import requests
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
import os


title = ""
overview = ""
genre = ""
img_link = ""
movielist = []
app = Flask(__name__)
Bootstrap5(app)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

# app.config['SECRET_KEY'] = 'mysecretKeyYY'


class Base(DeclarativeBase):
    pass
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///data.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)



login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# CONFIGURE TABLES
class Watched(db.Model):
    __tablename__ = "watched"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    overview: Mapped[str] = mapped_column(String(5000), nullable=False)
    genre: Mapped[str] = mapped_column(String(500), nullable=False)
    img_link: Mapped[str] = mapped_column(String(5000), nullable=False)

class Watchlist(db.Model):
    __tablename__ = "watchlist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    overview: Mapped[str] = mapped_column(String(5000), nullable=False)
    genre: Mapped[str] = mapped_column(String(500), nullable=False)
    img_link: Mapped[str] = mapped_column(String(5000), nullable=False)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))



with app.app_context():
    db.create_all()



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/front")
@login_required
def front():
    print(current_user.name)
    return render_template("front.html",data=current_user,flag=1)



@app.route("/moviecheck", methods=["GET","POST"])
@login_required
def moviecheck():
    global movielist
    movielist.clear()
    url = f"https://moviedatabase8.p.rapidapi.com/Search/{request.form['moviename']}"
    print(request.form['moviename'])
    headers = {
        "x-rapidapi-key": "9541fc81fdmsh0dd9ff43af7043cp109038jsn00c572831b28",
	"x-rapidapi-host": "moviedatabase8.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    movielist = response.json()
    return render_template("moviecheck.html", lists=response.json())

@app.route("/")
def home():
    if current_user.is_authenticated:
        return render_template("front.html",data=current_user,flag=1)
    return render_template("home.html")

@app.route("/login",methods=["POST","GET"])
def login():
    if request.method == "POST":
        password = request.form["password"]
        result = db.session.execute(db.select(User).where(User.email == request.form["email"]))

        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('front'))
    return render_template("login.html")


@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":

        user = db.session.execute(db.select(User).where(User.email == request.form['email'])).scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form['password'],
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form['email'],
            name=request.form['name'],
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('front'))
    return render_template("signup.html")

@app.route("/addwatched/<id>")
@login_required
def addwatched(id):
    global movielist
    global title
    global overview
    global genre
    global img_link
    for item in movielist:
        if str(item['_id']).__eq__(str(id)):
            title = item['title']
            overview = item['overview']
            genre = item['genres']
            img_link = item['poster_path']
            break


    movie = db.session.execute(
        db.select(Watched).where(Watched.user_id == current_user.id).where(Watched.overview == overview)).scalar()
    if movie:
        return redirect(url_for('watched'))

    new_movie = Watched(
        title = title,
        overview = overview,
        genre = genre,
        img_link = img_link,
        user_id = current_user.id
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('watched'))

@app.route("/removewatched/<moviename>")
@login_required
def removewatched(moviename):

    data_to_delete = db.session.execute(
        db.select(Watched).where(Watched.user_id == current_user.id).where(Watched.title == str(moviename))).scalar()
    db.session.delete(data_to_delete)
    db.session.commit()
    return redirect(url_for('watched'))



@app.route("/addwatchlist/<id>")
@login_required
def addwatchlist(id):
    global movielist
    global title
    global overview
    global genre
    global img_link
    for item in movielist:
        if str(item['_id']).__eq__(str(id)):
            title = item['title']
            overview = item['overview']
            genre = item['genres']
            img_link = item['poster_path']
            break


    movie = db.session.execute(
        db.select(Watchlist).where(Watchlist.user_id == current_user.id).where(Watchlist.overview == overview)).scalar()
    if movie:
        return redirect(url_for('watchlist'))

    new_movie = Watchlist(
        title=title,
        overview=overview,
        genre=genre,
        img_link=img_link,
        user_id = current_user.id
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('watchlist'))


@app.route("/removewatchlist/<moviename>")
@login_required
def removewatchlist(moviename):
    data_to_delete = db.session.execute(
        db.select(Watchlist).where(Watchlist.user_id == current_user.id).where(Watchlist.title == str(moviename))).scalar()
    db.session.delete(data_to_delete)
    db.session.commit()
    return redirect(url_for('watchlist'))



@app.route("/watched")
@login_required
def watched():
    watched_movies = db.session.execute(
        db.select(Watched).where(Watched.user_id == current_user.id)).scalars()
    return render_template("watched.html",movies=watched_movies)



@app.route("/watchlist")
@login_required
def watchlist():
    watchlist_movies = db.session.execute(
        db.select(Watchlist).where(Watchlist.user_id == current_user.id)).scalars()
    return render_template("watchlist.html", movies=watchlist_movies)


if __name__ == "__main__":
    app.run(debug=False)
