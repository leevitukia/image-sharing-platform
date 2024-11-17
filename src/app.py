from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from sqlalchemy import text
import bcrypt
from werkzeug.datastructures.file_storage import FileStorage
import subprocess
import random
import string
import datetime
import os
import io
import re


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = getenv("FLASK_SECRET_KEY")

db = SQLAlchemy(app)


@app.route("/")
def index():
    if("username" in session):
        if(checkIfUserExists(session["username"])):
            return render_template("indexLoggedIn.html", user=session["username"])
        else:
            del session["username"]
    return render_template("index.html")

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

        if checkIfUserExists(username):
            flash("Username already taken, please choose a different one.", "danger")
            return redirect("/signup")
        
        sql = text("INSERT INTO users (username, password) VALUES (:username, :password);")
        db.session.execute(sql, {"username": username, "password": hashed_password})
        db.session.commit()
        session["username"] = username
        return redirect("/")
    
    return render_template("create.html")

@app.route("/logout", methods=["GET"])
def logout():
    del session["username"]
    return redirect("/")

@app.route("/<string:user>")
def page(user):
    if(not checkIfUserExists(user)):
        return "This user doesn't exist"
    posts = getPostsByUser(user)
    return render_template("page.html", user=user, loggedInUser = session["username"], post_ids = posts)

@app.route("/<string:user>/post/<int:postId>")
def post(user, postId):
    description = getDescription(postId)
    return render_template("post.html", postId=postId, description=description)

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

        sql = text("INSERT INTO posts (content, attached_image, user_id, sent_at) VALUES (:description, :attached_image, :user_id, :sent_at) RETURNING id;")
        result = db.session.execute(sql, {"description": description, "attached_image": avifImage, "user_id": getUserID(username), "sent_at": datetime.datetime.utcnow()})
        db.session.commit()
        postId = result.scalar()
        return redirect(f"/{username}/post/{postId}")
    return render_template("upload.html")

def hash_password(pwd: str) -> str:
    salt = bcrypt.gensalt()
    hashedPwd = bcrypt.hashpw(pwd.encode(), salt).decode()
    return hashedPwd

def getUserID(username: str) -> int:
    result = db.session.execute(text("SELECT id FROM users WHERE username = :username LIMIT 1"),{"username": username}).fetchone()
    if result == None:
        return -1
    return result[0]

def processImage(image: FileStorage) -> bytes | None: # encodes an image to the AVIF format using the reference AV1 encoder through FFmpeg
    tempFile = f"{''.join(random.choices(string.ascii_uppercase, k=40))}.avif"
    fileBytes: bytes = image.stream.read()
    resolution = getImageResolution(fileBytes)
    if(resolution == None or resolution[0] > 8192 or resolution[1] > 8192):
        return None
    
    process = subprocess.Popen(
        f"ffmpeg -hide_banner -loglevel error -i - -an -frames:v 1 -c:v libaom-av1 -cpu-used 5 -still-picture 1 -pix_fmt yuv444p -aom-params aq-mode=1:enable-chroma-deltaq=1 -crf 30 -f avif {tempFile}".split(" "), 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    stdout, stderr = process.communicate(input=fileBytes)

    if(len(stderr.decode().strip()) != 0):
        print(stderr.decode().strip())
        os.remove(tempFile)
        return None
    with open(tempFile, 'rb') as file:
        file_data = file.read()

    os.remove(tempFile)

    return file_data
    

def getPostsByUser(username: str) -> list[int]:
    userId: int = getUserID(username)
    result = db.session.execute(text("SELECT id FROM posts WHERE user_id = :user_id"),{"user_id": userId}).scalars().fetchall()
    print(result)
    return result

def getImage(postId: int) -> bytes | None:
    result = db.session.execute(text("SELECT attached_image FROM posts WHERE id = :id LIMIT 1"),{"id": postId}).fetchone()
    if(result == None):
        return None
    return result[0]

def getDescription(postId: int) -> str | None:
    result = db.session.execute(text("SELECT content FROM posts WHERE id = :id LIMIT 1"),{"id": postId}).fetchone()
    if(result == None):
        return None
    return result[0]

def checkIfUserExists(username: str) -> bool:
    result = db.session.execute(text("SELECT 1 FROM users WHERE username = :username LIMIT 1"),{"username": username})
    return result.fetchone() != None

def checkCredentials(user: str, pwd: str) -> bool:
    result = db.session.execute(text("SELECT password FROM users WHERE username = :username LIMIT 1"),{"username": user}).fetchone()
    if result == None:
        return False
    hashedPwd: str = result[0]
    return bcrypt.checkpw(pwd.encode(), hashedPwd.encode())


def getImageResolution(file: bytes) -> tuple[int, int] | None: # I know there's much easier ways to do this but I wanna support extracting the first frame of a video 
    process = subprocess.Popen(
        f"ffmpeg -hide_banner -i -".split(" "), 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    stdout, stderr = process.communicate(input=file)

    pattern = r'(\d+)x(\d+)'
    match = re.search(pattern, stderr.decode().strip())

    if match:
        width, height = match.groups()
        return (int(width), int(height))
    else:
        return None