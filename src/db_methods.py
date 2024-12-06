from sqlalchemy import text
from config import db
import bcrypt

def getUserID(username: str) -> int:
    result = db.session.execute(text("SELECT id FROM users WHERE username = :username LIMIT 1"),{"username": username}).fetchone()
    if result == None:
        return -1
    return result[0]

def getUsername(userId: int) -> str:
    result = db.session.execute(text("SELECT username FROM users WHERE id = :id LIMIT 1"),{"id": userId}).fetchone()
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

def checkIfUsernameExists(username: str) -> bool:
    result = db.session.execute(text("SELECT 1 FROM users WHERE username = :username LIMIT 1"),{"username": username})
    return result.fetchone() != None

def checkIfUserIDExists(userId: int) -> bool:
    result = db.session.execute(text("SELECT 1 FROM users WHERE id = :id LIMIT 1"),{"id": userId})
    return result.fetchone() != None

def checkCredentials(user: str, pwd: str) -> bool:
    result = db.session.execute(text("SELECT password FROM users WHERE username = :username LIMIT 1"),{"username": user}).fetchone()
    if result == None:
        return False
    hashedPwd: str = result[0]
    return bcrypt.checkpw(pwd.encode(), hashedPwd.encode())

def getFavorites(user: str) -> list[str]:
    sql = text("SELECT username FROM users WHERE id IN (SELECT unnest(favorites) FROM users WHERE username = :username)")
    result = db.session.execute(sql, {"username": user}).scalars().all()
    if(result == None):
        return []
    return result

def deletePost(postId: int) -> None:
    db.session.execute(text("DELETE FROM comments WHERE post = :postId"), {"postId": postId})
    db.session.execute(text("DELETE FROM posts WHERE id = :postId"), {"postId": postId})
    db.session.commit()

def addToFavorites(user: str, userToAdd: str) -> None:
    sql = text("UPDATE users SET favorites = array_append(COALESCE(favorites, '{}'), :userToAdd) WHERE username = :username")
    db.session.execute(sql, {"userToAdd": getUserID(userToAdd), "username": user})
    db.session.commit()

def removeFromFavorites(user: str, userToRemove: str) -> None:
    sql = text("UPDATE users SET favorites = array_remove(COALESCE(favorites, '{}'), :userToRemove) WHERE username = :username")
    db.session.execute(sql, {"userToRemove": getUserID(userToRemove), "username": user})
    db.session.commit()

def createAccount(username: str, hashedPwd: str) -> None:
    sql = text("INSERT INTO users (username, password, profilePicture) VALUES (:username, :password, :pfp) RETURNING id;")
    defaultPfp: bytes = None
    with open("static/defaultPfp.avif", "rb") as file:
        defaultPfp = file.read()
    result = db.session.execute(sql, {"username": username, "password": hashedPwd, "pfp": defaultPfp})
    db.session.commit()
    return result.scalar()

def getPfp(username: str) -> bytes:
    result = db.session.execute(text("SELECT profilePicture FROM users WHERE username = :username LIMIT 1"),{"username": username})
    if(result == None):
        return None
    return result.scalar()

def addPostToDB(userId: int, description: str, attachedImage: bytes, thumbnail: bytes):
    imgSql = text("INSERT INTO images (attached_image, thumbnail) VALUES (:attached_image, :thumbnail) RETURNING id;")
    imageId = db.session.execute(imgSql, {"attached_image": attachedImage, "thumbnail": thumbnail}).scalar()

    sql = text("INSERT INTO posts (content, images, user_id) VALUES (:description, :images, :user_id) RETURNING id;")
    result = db.session.execute(sql, {"description": description, "images": imageId, "user_id": userId})
    db.session.commit()
    return result

def changeUsername(userId: int, newUsername: str) -> None:
    sql = text("UPDATE users SET username = :newUsername WHERE id = :id")
    db.session.execute(sql, {"newUsername": newUsername, "id": userId})
    db.session.commit()

def changeProfilePicture(userId: int, pfp: bytes) -> None:
    if(type(pfp) == type(None)):
        return
    sql = text("UPDATE users SET profilePicture = :pfp WHERE id = :id")
    db.session.execute(sql, {"pfp": pfp, "id": userId})
    db.session.commit()

def findUsers(query: str):
    modifiedQuery = f"{query.replace('%', '')}%"
    result = db.session.execute(text("SELECT username FROM users WHERE username iLIKE :query LIMIT 50"),{"query": modifiedQuery}).scalars()
    return [] if result == None else result

def sendMessage(message: str, fromUser: int, toUser: int):
    sql = text("INSERT INTO messages (content, sent_by, sent_to) VALUES (:content, :sent_by, :sent_to);")
    db.session.execute(sql, {"content": message, "sent_by": fromUser, "sent_to": toUser})
    db.session.commit()

def getMessages(user1: int, user2: int):
    sql = text("SELECT content, sent_by, sent_to, sent_at FROM messages WHERE (sent_by = :user1 AND sent_to = :user2) OR (sent_to = :user1 AND sent_by = :user2) ORDER BY sent_at ASC")
    result = db.session.execute(sql,{"user1": user1, "user2": user2}).fetchall()
    return [] if result == None else result

def getMessagedUsers(userId: int):
    sql = text("SELECT username FROM users WHERE id IN (SELECT DISTINCT sent_to FROM messages WHERE sent_by = :userId) OR id IN (SELECT DISTINCT sent_by FROM messages WHERE sent_to = :userId)")
    result = db.session.execute(sql, {"userId": userId}).scalars().all()
    return result
        
def getComments(postId: int):
    sql = text("SELECT content, user_id, sent_at FROM comments WHERE post = :post ORDER BY sent_at ASC")
    result = db.session.execute(sql,{"post": postId}).fetchall()
    if(result == None):
        return []
    return [{"content": comment.content, "username": getUsername(comment.user_id), "sent_at": comment.sent_at} for comment in result]
    
def addComment(comment: str, userId: int, postId: int):
    sql = text("INSERT INTO comments (content, post, user_id) VALUES (:content, :post, :user_id);")
    db.session.execute(sql, {"content": comment, "post": postId, "user_id": userId})
    db.session.commit()

def checkIfPostExists(postId: int, userId: int) -> bool:
    sql = text("SELECT 1 FROM posts WHERE id = :id AND user_id = :user_id LIMIT 1")
    result = db.session.execute(sql,{"id": postId, "user_id": userId}).fetchall()
    return len(result) != 0