from flask import Flask, flash, redirect, render_template, request, session, send_file
from os import getenv
from sqlalchemy import text
import bcrypt
import io
from db_methods import checkCredentials, checkIfUserExists, getDescription, addToFavorites, removeFromFavorites, deletePost, getFavorites, getPostsByUser, getImage, createAccount, addPostToDB
from image_processing import processImage

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = getenv("FLASK_SECRET_KEY")

@app.route("/")
def index():
    if("username" in session and not checkIfUserExists(session["username"])):
        del session["username"]
    loggedInUser = session["username"] if "username" in session else None
    return render_template("index.html", user=loggedInUser)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["pwd"]
        if(checkCredentials(username, password)):
            session["username"] = username
            return redirect("/")
        else:
            flash("Incorrect password or username", "danger")
            return redirect("/login")
        
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["pwd"]

        hashed_password = hash_password(password)

        if(checkIfUserExists(username)):
            flash("Username already taken, please choose a different one.", "danger")
            return redirect("/signup")
        
        createAccount(username, hashed_password)
        session["username"] = username
        return redirect("/")
    
    return render_template("create.html")

@app.route("/logout", methods=["GET"])
def logout():
    del session["username"]
    return redirect("/")

@app.route("/<string:user>", methods=["GET", "POST"])
def page(user):
    if(not checkIfUserExists(user)):
        return "This user doesn't exist"
    posts = getPostsByUser(user)
    loggedInUser = session["username"]

    favorites = getFavorites(loggedInUser)
    isFavorited = user in favorites
    if(request.method == "POST"):
        if(isFavorited):
            removeFromFavorites(loggedInUser, user)
        else:
            addToFavorites(loggedInUser, user)
        isFavorited = not isFavorited

    return render_template("page.html", user=user, loggedInUser = loggedInUser, post_ids = posts, favorited = isFavorited)


@app.route("/<string:user>/favorites")
def favorites(user):
    loggedInUser = session["username"]
    if(not checkIfUserExists(user)):
        return "This user doesn't exist"
    if(user != loggedInUser):
        return "Access Denied"
    
    users = getFavorites(user)
    return render_template("favorites.html", users = users, user = user)


@app.route("/<string:user>/post/<int:postId>", methods=["GET", "POST"])
def post(user, postId):
    loggedInUser = session["username"]
    if request.method == "POST" and user == loggedInUser:
        deletePost(postId)
        return redirect(f"/{user}")
    else:
        description = getDescription(postId)
        return render_template("post.html", postId=postId, description=description, loggedInUser=loggedInUser, user=user)

@app.route('/post<int:postId>.avif') #dynamic image url
def postImage(postId):
    image = getImage(postId)
    if(image == None):
        return ""
    
    return send_file(io.BytesIO(image), "image/avif", download_name=f"{postId}.avif")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST" and checkIfUserExists(session["username"]):
        if 'file' not in request.files:
            flash('No file')
            return redirect(request.url)
        file = request.files['file']

        avifImage: bytes = processImage(file)
        
        if(avifImage == None):
            flash('Invalid file')
            return redirect(request.url)
        description = request.form["description"]
        username = session["username"]

        result = addPostToDB()
        postId = result.scalar()
        return redirect(f"/{username}/post/{postId}")
    return render_template("upload.html")

def hash_password(pwd: str) -> str:
    salt = bcrypt.gensalt()
    hashedPwd = bcrypt.hashpw(pwd.encode(), salt).decode()
    return hashedPwd
