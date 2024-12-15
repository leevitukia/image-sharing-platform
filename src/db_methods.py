from sqlalchemy import text
import bcrypt
from config import db

def get_user_id(username: str) -> int:
    result = db.session.execute(text("SELECT id FROM users WHERE username = :username LIMIT 1"),{"username": username}).fetchone()
    if result is None:
        return -1
    return result[0]

def get_username(user_id: int) -> str:
    result = db.session.execute(text("SELECT username FROM users WHERE id = :id LIMIT 1"),{"id": user_id}).fetchone()
    if result is None:
        return -1
    return result[0]

def get_posts_by_user(username: str) -> list[int]:
    user_id: int = get_user_id(username)
    result = db.session.execute(text("SELECT id FROM posts WHERE user_id = :user_id"),{"user_id": user_id}).scalars().fetchall()
    return result

def get_image(post_id: int) -> bytes | None:
    image_id = db.session.execute(text("SELECT images FROM posts WHERE id = :id LIMIT 1"),{"id": post_id}).scalar()
    result = db.session.execute(text("SELECT attached_image FROM images WHERE id = :id LIMIT 1"),{"id": image_id}).fetchone()
    if result is None:
        return None
    return result[0]

def get_thumbnail(post_id: int) -> bytes | None:
    image_id = db.session.execute(text("SELECT images FROM posts WHERE id = :id LIMIT 1"),{"id": post_id}).scalar()
    result = db.session.execute(text("SELECT thumbnail FROM images WHERE id = :id LIMIT 1"),{"id": image_id}).fetchone()
    if result is None:
        return None
    return result[0]

def get_description(post_id: int) -> str | None:
    result = db.session.execute(text("SELECT content FROM posts WHERE id = :id LIMIT 1"),{"id": post_id}).fetchone()
    if result is None:
        return None
    return result[0]

def check_if_username_exists(username: str) -> bool:
    result = db.session.execute(text("SELECT 1 FROM users WHERE username = :username LIMIT 1"),{"username": username})
    return result.fetchone() is not None

def check_if_user_id_exists(user_id: int) -> bool:
    result = db.session.execute(text("SELECT 1 FROM users WHERE id = :id LIMIT 1"),{"id": user_id})
    return result.fetchone() is not None

def check_credentials(user: str, pwd: str) -> bool:
    result = db.session.execute(text("SELECT password FROM users WHERE username = :username LIMIT 1"),{"username": user}).fetchone()
    if result is None:
        return False
    hashed_password: str = result[0]
    return bcrypt.checkpw(pwd.encode(), hashed_password.encode())

def get_favorites(user: str) -> list[str]:
    sql = text("SELECT username FROM users WHERE id IN (SELECT unnest(favorites) FROM users WHERE username = :username)")
    result = db.session.execute(sql, {"username": user}).scalars().all()
    if result is None:
        return []
    return result

def delete_post(post_id: int) -> None:
    db.session.execute(text("DELETE FROM comments WHERE post = :post_id"), {"post_id": post_id})
    db.session.execute(text("DELETE FROM posts WHERE id = :post_id"), {"post_id": post_id})
    db.session.commit()

def add_to_favorites(user: str, user_to_add: str) -> None:
    sql = text("UPDATE users SET favorites = array_append(COALESCE(favorites, '{}'), :userToAdd) WHERE username = :username")
    db.session.execute(sql, {"userToAdd": get_user_id(user_to_add), "username": user})
    db.session.commit()

def remove_from_favorites(user: str, user_to_remove: str) -> None:
    sql = text("UPDATE users SET favorites = array_remove(COALESCE(favorites, '{}'), :userToRemove) WHERE username = :username")
    db.session.execute(sql, {"userToRemove": get_user_id(user_to_remove), "username": user})
    db.session.commit()

def create_account(username: str, password: str) -> None:
    sql = text("INSERT INTO users (username, password, profilePicture) VALUES (:username, :password, :pfp) RETURNING id;")
    default_pfp: bytes = None
    with open("static/defaultPfp.avif", "rb") as file:
        default_pfp = file.read()

    hashed_password = hash_password(password)

    result = db.session.execute(sql, {"username": username, "password": hashed_password, "pfp": default_pfp})
    db.session.commit()
    return result.scalar()

def hash_password(pwd: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd.encode(), salt).decode()
    return hashed_password


def get_pfp(username: str) -> bytes:
    result = db.session.execute(text("SELECT profilePicture FROM users WHERE username = :username LIMIT 1"),{"username": username})
    if result is None:
        return None
    return result.scalar()

def add_post_to_db(user_id: int, description: str, post_image: bytes, thumbnail: bytes):
    img_sql = text("INSERT INTO images (attached_image, thumbnail) VALUES (:attached_image, :thumbnail) RETURNING id;")
    image_id = db.session.execute(img_sql, {"attached_image": post_image, "thumbnail": thumbnail}).scalar()

    sql = text("INSERT INTO posts (content, images, user_id) VALUES (:description, :images, :user_id) RETURNING id;")
    result = db.session.execute(sql, {"description": description, "images": image_id, "user_id": user_id})
    db.session.commit()
    return result

def change_username(user_id: int, new_username: str) -> None:
    sql = text("UPDATE users SET username = :newUsername WHERE id = :id")
    db.session.execute(sql, {"newUsername": new_username, "id": user_id})
    db.session.commit()

def change_profile_picture(user_id: int, pfp: bytes) -> None:
    if pfp is None:
        return
    sql = text("UPDATE users SET profilePicture = :pfp WHERE id = :id")
    db.session.execute(sql, {"pfp": pfp, "id": user_id})
    db.session.commit()

def find_users(query: str):
    modified_query = f"{query.replace('%', '')}%"
    result = db.session.execute(text("SELECT username FROM users WHERE username iLIKE :query LIMIT 50"),{"query": modified_query}).scalars()
    return [] if result is None else result

def send_message(message: str, sent_by: int, sent_to: int):
    sql = text("INSERT INTO messages (content, sent_by, sent_to) VALUES (:content, :sent_by, :sent_to);")
    db.session.execute(sql, {"content": message, "sent_by": sent_by, "sent_to": sent_to})
    db.session.commit()

def get_messages(user1: int, user2: int):
    sql = text(("SELECT content, sent_by, sent_to, sent_at FROM messages WHERE (sent_by = :user1 AND sent_to = :user2)"
               "OR (sent_to = :user1 AND sent_by = :user2) ORDER BY sent_at ASC"))
    result = db.session.execute(sql,{"user1": user1, "user2": user2}).fetchall()
    return [] if result is None else result

def get_messaged_users(user_id: int):
    sql = text(("SELECT username FROM users WHERE id IN (SELECT DISTINCT sent_to FROM messages WHERE sent_by = :user_id)"
               "OR id IN (SELECT DISTINCT sent_by FROM messages WHERE sent_to = :user_id)"))
    result = db.session.execute(sql, {"user_id": user_id}).scalars().all()
    return result

def get_comments(post_id: int):
    sql = text("SELECT content, user_id, sent_at FROM comments WHERE post = :post ORDER BY sent_at ASC")
    result = db.session.execute(sql,{"post": post_id}).fetchall()
    if result is None:
        return []
    return [{"content": comment.content, "username": get_username(comment.user_id), "sent_at": comment.sent_at} for comment in result]

def add_comment(comment: str, user_id: int, post_id: int):
    sql = text("INSERT INTO comments (content, post, user_id) VALUES (:content, :post, :user_id);")
    db.session.execute(sql, {"content": comment, "post": post_id, "user_id": user_id})
    db.session.commit()

def check_if_post_exists(post_id: int, user_id: int) -> bool:
    sql = text("SELECT 1 FROM posts WHERE id = :id AND user_id = :user_id LIMIT 1")
    result = db.session.execute(sql,{"id": post_id, "user_id": user_id}).fetchall()
    return len(result) != 0
