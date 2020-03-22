import csv
import os
import math

from docxtpl import DocxTemplate
from datetime import date

from flask import Flask, render_template, url_for, redirect, request, send_file
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_fontawesome import FontAwesome

from wtforms import TextAreaField, StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, InputRequired, Email, Length, NumberRange
from wtforms import validators, ValidationError
from flask_wtf.file import FileField, FileRequired, FileAllowed

from werkzeug.security import generate_password_hash, check_password_hash

from geopy.distance import geodesic


basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = "./uploads"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'short-term-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'mydatabase.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
fa = FontAwesome(app)


##### Define Forms #######
class LoginForm(FlaskForm):
    email = StringField(
        "Email-Adresse", validators=[DataRequired()], id="id_email")
    password = PasswordField('Passwort', validators=[
                             DataRequired()], id="id_password")
    remember_me = BooleanField('Angemeldet bleiben', id="id_remember")
    submit = SubmitField('Anmelden')


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email(
        message="Invalid email"), Length(max=50)])
    username = StringField("Username", validators=[
                           InputRequired(), Length(min=4, max=15)])
    password = PasswordField("Password", validators=[
                             InputRequired(), Length(min=8, max=80)])


class CreatePageForm(FlaskForm):
    artist_name = StringField(
        "Name", validators=[DataRequired("Bitte gib Deinen Namen an.")])
    artist_category = SelectField("Kategorie", [DataRequired("Bitte wähle eine Kategorie aus.")], choices=[
                                  ('Musik', 'Musik'), ('Bildende Künste', 'Bildende Künste'), ('Schauspiel', 'Schauspiel')])
    artist_job = StringField(
        "Job", [DataRequired("Bitte gib Deinen Job an.")])
    titlepicture_path = FileField("Profilbild")
    artist_location = StringField(
        "Wohnort", [DataRequired("Bitte gib Deinen Wohnort an.")], id="addressfield")
    description_title = StringField(
        "Titel", [DataRequired("Bitte gib einen Titel an.")])
    description_general = TextAreaField(
        "Steckbrief", [DataRequired("Bitte stelle Dich kurz vor.")])
    description_crisis = TextAreaField("Beschreibung Deiner Lage zu Zeiten COVID-19s", [
        DataRequired("Bitte beschreibe Deine Lage.")])
    description_rewards = TextAreaField("Beschreibung Deiner Angebote")
    artist_location_long = FloatField(id="secretlng")
    artist_location_lat = FloatField(id="secretlat")
    submit = SubmitField('Absenden')

class CreateRewardForm(FlaskForm):
    title = StringField(
        "Titel", [DataRequired(message="Bitte gib einen Titel an.")])
    description = StringField(
        "Beschreibung", [DataRequired(message="Bitte gib eine Beschreibung an.")])
    category_form = SelectField("Kategorie", [DataRequired(message="Bitte wähle eine Kategorie aus.")], choices=[
                                  ('Virtuell', 'Virtuell'), ('Analog', 'Analog')])
    category_time = SelectField("Wann kann der Voucher eingelöst werden?", [DataRequired(message="Bitte wähle einen Zeitraum aus.")], choices=[
        ('ab sofort', 'ab sofort'), ('nach der Krise', 'nach der Krise')])
    price = IntegerField(
        "Preis (in €)", [DataRequired(message="Bitte gib einen Preis an.")])
    number = IntegerField("Wie viele dieser Voucher willst du anbieten?", validators=[
                                  DataRequired(message="Bitte gib eine Anzahl an."), NumberRange(min=0)])
    submit = SubmitField('Absenden')

class LocationForm(FlaskForm):
    location = StringField(id="addressfield")
    secretlng = FloatField(id="secretlng")
    secretlat = FloatField(id="secretlat")
    categories = SelectField("Kategorie", choices=[('Alle', 'Alle'), ('Musik', 'Musik'), ('Bildende Künste', 'Bildende Künste'), ('Schauspiel', 'Schauspiel')])

#### Define Database Tables #######
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    pages = db.relationship('Page', backref='creator', lazy=True)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    artist_name = db.Column(db.String)
    artist_category = db.Column(db.String)
    artist_job = db.Column(db.String)
    artist_location_lat = db.Column(db.Float)
    artist_location_long = db.Column(db.Float)

    description_title = db.Column(db.String)
    description_general = db.Column(db.String)
    description_crisis = db.Column(db.String)
    description_rewards = db.Column(db.String)

    # Filepaths
    titlepicture_path = db.Column(db.String)
    media_path = db.Column(db.String)

    rewards = db.relationship('Reward', backref='Page', lazy=True)


class Reward(db.Model):
    Page_Id = db.Column(db.Integer, db.ForeignKey("page.id"))
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    category_form = db.Column(db.String)
    category_time = db.Column(db.String)
    price = db.Column(db.Float)
    primary = db.Column(db.Boolean)
    active = db.Column(db.Boolean)


##### Necessary WebApp Definitions ######
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Page': Page, 'Reward': Reward}


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def distanceMath(lat1, lat2, lon1, lon2):
    Ort1 = (lat1, lon1)
    Ort2 = (lat2, lon2)

    distance = round(geodesic(Ort1, Ort2).km, 2)
    return distance
######## Routes ##########
@app.route("/index", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    form = LocationForm()
    if form.validate_on_submit():
        return f"<h1>{form.location.data}<h1>"
    return render_template("index.html", title="Home", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method="sha256")
        new_user = User(username=form.username.data,
                        email=form.email.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))

    return render_template("signup.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            return render_template("login.html", title="Anmelden", form=form)

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))

    return render_template("login.html", title="Anmelden", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/createPage", methods=['GET', 'POST'])
@login_required
def createPage():
    form = CreatePageForm()
    
    if form.validate_on_submit():
      f = form.titlepicture_path.data
      filename = f.filename
      f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

      page = Page()
      form.populate_obj(page)

      page.titlepicture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

      page.creator_id = current_user.id
      
      db.session.add(page)
      db.session.commit()

      id_for_rewards = Page.query.filter_by(description_general=page.description_general)
      return redirect(url_for('createReward', pageId=id_for_rewards.id))
    
    return render_template("createPage.html", title="Seite erstellen", form=form)

@app.route("/createRewards/<int:pageId>", methods=['GET', 'POST'])
@login_required
def createRewards(pageId):
    rewards = Reward.query.filter_by(Page_Id=pageId)
    form = CreateRewardForm()
    
    if form.validate_on_submit():
        r = Reward()
        form.populate_obj(r)
        r.Page_Id = pageId
        
        db.session.add(r)
        db.session.commit()
        return render_template("createRewards.html", title="Angebote erstellen", form=form, rewards=rewards)
        
    return render_template("createRewards.html", title="Angebote erstellen", form=form, rewards=rewards)


@app.route("/deletePage", methods=['GET', 'POST'])
@login_required
def deletePage():
    return "<h1>In Process<h1>"

@app.route("/listPages", methods=['GET', 'POST'])
def listPages():
    form = LocationForm()
    distances = {}
    if form.validate_on_submit():
        distances = {}
        if form.categories.data == "Alle":
            pages = db.session.query(Page.id, Page.artist_name, Page.artist_job, Page.titlepicture_path, Page.artist_location_lat, Page.artist_location_long)
            for page in pages:
                distances[page] = distanceMath(form.secretlat.data, page.artist_location_lat, form.secretlng.data, page.artist_location_long)
                distances_sorted = {k: v for k, v in sorted(distances.items(), key=lambda x: x[1])}
        else:
            pages = db.session.query(Page.id, Page.artist_name, Page.artist_job, Page.titlepicture_path, Page.artist_location_lat, Page.artist_location_long).filter(Page.artist_category == form.categories.data)
            for page in pages:
                distances[page] = distanceMath(form.secretlat.data, page.artist_location_lat, form.secretlng.data, page.artist_location_long)    
                distances_sorted = {k: v for k, v in sorted(distances.items(), key=lambda x: x[1])}

        
        
        return render_template("listPages.html", title="Übersicht", distances=distances_sorted, form=form)
    pages = db.session.query(Page.id, Page.artist_name, Page.artist_job, Page.titlepicture_path, Page.artist_location_lat, Page.artist_location_long)
    return render_template("listPages.html", title="Übersicht", distances=pages, form=form)

@app.route("/page/<int:PageId>")
def page(PageId):
    pageName = "Test"
    page = Page.query.filter_by(id = PageId).first()
    rewards = Reward.query.filter(Reward.Page_Id == PageId).order_by(Reward.price.asc())


    return render_template("page.html", title=f"{pageName}", page=page, rewards=rewards)


@app.route("/test")
def test():
    form = CreateVoucherForm()
    return render_template("test.html", title="test", form=form)


if __name__ == "__main__":
    app.run(debug=True)

