from sqlalchemy import text, Result
from flask_sqlalchemy import SQLAlchemy
from config import db
import bcrypt
import datetime

def getUserID(username: str) -> int:
    result = db.session.execute(text("SELECT id FROM users WHERE username = :username LIMIT 1"),{"username": username}).fetchone()
    if result == None:
        return -1
    return result[0]

def getPostsByUser(username: str) -> list[int]:
    userId: int = getUserID(username)
    result = db.session.execute(text("SELECT id FROM posts WHERE user_id = :user_id"),{"user_id": userId}).scalars().fetchall()
    return result

def getImage(postId: int) -> bytes | None:
    imageId = db.session.execute(text("SELECT images FROM posts WHERE id = :id LIMIT 1"),{"id": postId}).scalar()
    result = db.session.execute(text("SELECT attached_image FROM images WHERE id = :id LIMIT 1"),{"id": imageId}).fetchone()
    if(result == None):
        return None
    return result[0]

def getThumbnail(postId: int) -> bytes | None:
    imageId = db.session.execute(text("SELECT images FROM posts WHERE id = :id LIMIT 1"),{"id": postId}).scalar()
    result = db.session.execute(text("SELECT thumbnail FROM images WHERE id = :id LIMIT 1"),{"id": imageId}).fetchone()
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

def getFavorites(user: str) -> list[str]:
    result = db.session.execute(text("SELECT favorites FROM users WHERE username = :username LIMIT 1"),{"username": user}).scalar()
    return [] if result == None else result

def deletePost(postId: int) -> None:
    db.session.execute(text("DELETE FROM posts WHERE id = :postId"), {"postId": postId})
    db.session.commit()

def addToFavorites(user: str, userToAdd: str) -> None:
    sql = text("UPDATE users SET favorites = array_append(COALESCE(favorites, '{}'), :userToAdd) WHERE username = :username")
    db.session.execute(sql, {"userToAdd": userToAdd, "username": user})
    db.session.commit()

def removeFromFavorites(user: str, userToRemove: str) -> None:
    sql = text("UPDATE users SET favorites = array_remove(COALESCE(favorites, '{}'), :userToRemove) WHERE username = :username")
    db.session.execute(sql, {"userToRemove": userToRemove, "username": user})
    db.session.commit()

def createAccount(username: str, hashedPwd: str) -> None:
    sql = text("INSERT INTO users (username, password) VALUES (:username, :password);")
    db.session.execute(sql, {"username": username, "password": hashedPwd})
    db.session.commit()

def addPostToDB(username: str, description: str, attachedImage: bytes, thumbnail: bytes):
    imgSql = text("INSERT INTO images (attached_image, thumbnail) VALUES (:attached_image, :thumbnail) RETURNING id;")
    imageId = db.session.execute(imgSql, {"attached_image": attachedImage, "thumbnail": thumbnail}).scalar()

    sql = text("INSERT INTO posts (content, images, user_id) VALUES (:description, :images, :user_id) RETURNING id;")
    result = db.session.execute(sql, {"description": description, "images": imageId, "user_id": getUserID(username)})
    db.session.commit()
    return result