import secrets
import io
from flask import flash, redirect, render_template, request, session, send_file
from config import app
from db_methods import (check_if_user_id_exists, get_username, check_credentials, get_user_id, check_if_username_exists, get_posts_by_user,
                        create_account, remove_from_favorites, get_favorites, add_to_favorites, check_if_post_exists, delete_post, add_comment,
                        get_description, get_comments, get_image, get_thumbnail, get_pfp, add_post_to_db, change_username, change_profile_picture,
                        find_users, get_messaged_users, send_message, get_messages,
                        )
from image_processing import process_image, create_thumbnail

@app.route("/")
def index():
    if "userId" in session and not check_if_user_id_exists(session["userId"]):
        return logout()
    logged_in_user = get_username(session["userId"]) if "userId" in session else None
    return render_template("index.html", user=logged_in_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["pwd"]
        if check_credentials(username, password):
            session["userId"] = get_user_id(username)
            session["csrf"] = secrets.token_hex(16)
            return redirect("/")
        else:
            flash("Incorrect password or username", "danger")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["pwd"]

        if check_if_username_exists(username):
            flash("Username already taken, please choose a different one.", "danger")
            return redirect("/signup")
        elif len(username) >= 35:
            flash("Your username exceeds the maximum length, please choose one that's shorter than 35 characters.")
            return redirect("/signup")
        user_id = create_account(username, password)
        session["userId"] = user_id
        session["csrf"] = secrets.token_hex(16)
        return redirect("/")
    return render_template("create.html")

@app.route("/logout", methods=["GET"])
def logout():
    del session["userId"]
    del session["csrf"]
    return redirect("/")

@app.route("/user/<string:user>", methods=["GET", "POST"])
def page(user):
    if not check_if_username_exists(user):
        return "This user doesn't exist"
    posts = get_posts_by_user(user)
    logged_in_user = get_username(session["userId"])

    favorites = get_favorites(logged_in_user)
    is_favorited = user in favorites
    if request.method == "POST" and validate_csrf_token(request.form):
        if is_favorited:
            remove_from_favorites(logged_in_user, user)
        else:
            add_to_favorites(logged_in_user, user)
        return redirect(f"/user/{user}")

    return render_template("page.html", user=user, loggedInUser = logged_in_user, post_ids = posts, favorited = is_favorited)


@app.route("/favorites")
def favorites_page():
    user = get_username(session["userId"])
    if not check_if_username_exists(user):
        return "This user doesn't exist"
    users = get_favorites(user)
    return render_template("favorites.html", users = users, user = user)


@app.route("/user/<string:user>/post/<int:post_id>", methods=["GET", "POST"])
def post(user, post_id):
    if not check_if_post_exists(post_id, get_user_id(user)):
        return redirect(f"/user/{user}")

    logged_in_user = get_username(session["userId"])
    if request.method == "POST" and validate_csrf_token(request.form):
        if "delete" in request.form and user == logged_in_user:
            delete_post(post_id)
            return redirect(f"/user/{user}")
        elif "content" in request.form:
            add_comment(request.form["content"], session["userId"], post_id)
            return redirect(f"/user/{user}/post/{post_id}")

    description = get_description(post_id)
    comments = get_comments(post_id)
    return render_template("post.html", post_id=post_id, description=description, loggedInUser=logged_in_user, user=user, comments=comments)

@app.route('/post/<int:post_id>.avif') #dynamic image url
def post_image(post_id):
    image = get_image(post_id)
    if image is None:
        return ""
    return send_file(io.BytesIO(image), "image/avif", download_name=f"{post_id}.avif")

@app.route('/thumb/<int:post_id>.avif')
def post_thumbnail(post_id):
    image = get_thumbnail(post_id)
    if image is None:
        return ""
    return send_file(io.BytesIO(image), "image/avif", download_name=f"thumb{post_id}.avif")

@app.route('/pfp/<string:username>.avif')
def pfp(username):
    image = get_pfp(username)
    if image is None:
        return ""
    return send_file(io.BytesIO(image), "image/avif", download_name=f"{username}.avif")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST" and check_if_user_id_exists(session["userId"]) and validate_csrf_token(request.form):
        if 'file' not in request.files:
            flash("No file")
            return redirect("/upload")
        file = request.files['file']
        img_bytes: bytes = file.stream.read()

        avif_image: bytes = process_image(img_bytes)
        if avif_image is None:
            flash("Invalid file")
            return redirect("/upload")
        
        description = request.form["description"]

        if len(description) >= 300:
            flash("Your description is too long, please keep it below 300 characters")
            return redirect("/upload")

        thumbnail = create_thumbnail(img_bytes)

        user_id = session["userId"]
        username = get_username(user_id)

        result = add_post_to_db(user_id, description, avif_image, thumbnail)
        post_id = result.scalar()
        return redirect(f"/user/{username}/post/{post_id}")
    return render_template("upload.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    user_id = session["userId"]
    if not check_if_user_id_exists(user_id):
        return "You need to be logged in to change settings"
    username = get_username(user_id)

    if request.method == "POST" and validate_csrf_token(request.form):
        new_username = request.form["username"]
        if new_username != username and not check_if_username_exists(new_username):
            change_username(user_id, new_username)

        if "file" in request.files:
            file = request.files['file']
            if file.filename != '':
                img_bytes: bytes = file.stream.read()
                new_pfp = create_thumbnail(img_bytes)
                change_profile_picture(user_id, new_pfp)

        return redirect("/settings")
    return render_template("settings.html", username=username)

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form["query"]
        if query == "":
            return redirect("/search")
        return redirect(f"/search/{query}")
    query = ""
    users = find_users(query)
    return render_template("search.html", query=query, users=users)

@app.route("/search/<string:query>", methods=["GET"])
def searched(query: str):
    users = find_users(query)
    return render_template("search.html", query=query, users=users)


@app.route("/messages", methods=["GET"])
def messages():
    user_id = session["userId"]
    messaged_users = get_messaged_users(user_id)
    return render_template("messages.html", messagedUsers=messaged_users)

@app.route("/messages/<int:recipient_user_id>", methods=["GET", "POST"])
def conversation(recipient_user_id: str):
    user_id = session["userId"]
    if not check_if_user_id_exists(user_id):
        return redirect("/")
    recipient_username: str = get_username(recipient_user_id)

    if request.method == "POST" and validate_csrf_token(request.form):
        message = request.form["msgBox"]
        send_message(message, user_id, recipient_user_id)
        return redirect(f"/messages/{recipient_user_id}")

    all_messages = get_messages(user_id, recipient_user_id)

    return render_template("conversation.html", recipient=recipient_user_id, userName=recipient_username, messages=all_messages)

@app.route("/messages/<string:username>", methods=["GET"])
def conversation_redirect(username: str):
    user_id = get_user_id(username)
    return redirect(f"/messages/{user_id}")

def validate_csrf_token(form: dict) -> bool:
    csrf = form.get("csrf")
    if csrf is not None and csrf == session["csrf"]:
        return True
    return False
