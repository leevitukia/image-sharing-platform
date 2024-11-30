from flask import Flask, flash, redirect, render_template, request, session, send_file
from os import getenv
from sqlalchemy import text
import bcrypt
import io
from config import app, db
from db_methods import *
from image_processing import processImage, createThumbnail
from flask_sqlalchemy import SQLAlchemy


@app.route("/")
def index():
    if("userId" in session and not checkIfUserIDExists(session["userId"])):
        del session["userId"]
    loggedInUser = getUsername(session["userId"]) if "userId" in session else None
    return render_template("index.html", user=loggedInUser)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["pwd"]
        if(checkCredentials(username, password)):
            session["userId"] = getUserID(username)
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

        if(checkIfUsernameExists(username)):
            flash("Username already taken, please choose a different one.", "danger")
            return redirect("/signup")
        
        userId = createAccount(username, hashed_password)
        session["userId"] = userId
        return redirect("/")
    
    return render_template("create.html")

@app.route("/logout", methods=["GET"])
def logout():
    del session["userId"]
    return redirect("/")

@app.route("/<string:user>", methods=["GET", "POST"])
def page(user):
    if(not checkIfUsernameExists(user)):
        return "This user doesn't exist"
    posts = getPostsByUser(user)
    loggedInUser = getUsername(session["userId"])

    favorites = getFavorites(loggedInUser)
    isFavorited = getUserID(user) in favorites
    if(request.method == "POST"):
        if(isFavorited):
            removeFromFavorites(loggedInUser, user)
        else:
            addToFavorites(loggedInUser, user)
        isFavorited = not isFavorited

    return render_template("page.html", user=user, loggedInUser = loggedInUser, post_ids = posts, favorited = isFavorited)


@app.route("/<string:user>/favorites")
def favorites(user):
    loggedInUser = getUsername(session["userId"])
    if(not checkIfUsernameExists(user)):
        return "This user doesn't exist"
    if(user != loggedInUser):
        return "Access Denied"
    
    users = getFavorites(user)
    return render_template("favorites.html", users = users, user = user)


@app.route("/<string:user>/post/<int:postId>", methods=["GET", "POST"])
def post(user, postId):
    loggedInUser = getUsername(session["userId"])
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

@app.route('/thumb<int:postId>.avif')
def thumbnail(postId):
    image = getThumbnail(postId)
    if(image == None):
        return ""
    return send_file(io.BytesIO(image), "image/avif", download_name=f"thumb{postId}.avif")

@app.route('/<string:username>.avif')
def pfp(username):
    image = getPfp(username)
    if(image == None):
        return ""
    return send_file(io.BytesIO(image), "image/avif", download_name=f"{username}.avif")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST" and checkIfUsernameExists(session["userId"]):
        if 'file' not in request.files:
            flash('No file')
            return redirect(request.url)
        file = request.files['file']
        imgBytes: bytes = file.stream.read()

        avifImage: bytes = processImage(imgBytes)
        if(avifImage == None):
            flash('Invalid file')
            return redirect(request.url)
        thumbnail = createThumbnail(imgBytes)
        description = request.form["description"]
        userId = session["userId"]
        username = getUsername(userId)

        result = addPostToDB(userId, description, avifImage, thumbnail)
        postId = result.scalar()
        return redirect(f"/{username}/post/{postId}")
    return render_template("upload.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    userId = session["userId"]
    if(not checkIfUserIDExists(userId)):
        return "You need to be logged in to change settings"
    username = getUsername(userId)

    if(request.method == "GET"):
        return render_template("settings.html", username=username)
    elif(request.method == "POST"):
        newUsername = request.form["username"]
        if(newUsername != username and not checkIfUsernameExists(newUsername)):
            changeUsername(userId, newUsername)

        if("file" in request.files):
            file = request.files['file']
            imgBytes: bytes = file.stream.read()
            newPfp = createThumbnail(imgBytes)
            changeProfilePicture(userId, newPfp)

        return redirect("/settings")
    

def hash_password(pwd: str) -> str:
    salt = bcrypt.gensalt()
    hashedPwd = bcrypt.hashpw(pwd.encode(), salt).decode()
    return hashedPwd
