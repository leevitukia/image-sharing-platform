CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    attached_image BYTEA,
    thumbnail BYTEA
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    favorites INT ARRAY,
    profilePicture BYTEA
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    content TEXT,
    images INT REFERENCES images(id),
    user_id INT REFERENCES users(id),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT,
    post INT REFERENCES posts(id),
    user_id INT REFERENCES users(id),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    content TEXT,
    sent_by INT REFERENCES users(id),
    sent_to INT REFERENCES users(id),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_sent_at ON posts(sent_at);

CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_post ON comments(post);

CREATE INDEX idx_messages_sent_by ON messages(sent_by);
CREATE INDEX idx_messages_sent_to ON messages(sent_to);
