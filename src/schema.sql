
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    favorites TEXT ARRAY
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    content TEXT,
    attached_image BYTEA,
    user_id INT REFERENCES users(id),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON posts(user_id);
CREATE INDEX idx_sent_at ON posts(sent_at);
