# image-sharing-platform


### Features
- The user can create a new account or log in: Done
- The user can change their username and profile picture: Not implemented
- Users can post & delete images: Done
- Users can favorite other users' pages: Done
- Users can attach a caption/description to their images: Done
- Users can comment on posts: Not implemented
- Users can message other users: Not implemented
- Users can like posts: Not implemented
- Good looking UI: absolutely not done

###  How to test the app
1. Clone the repo
2. Create a Python 3.10 environment
3. Install the required packages with `pip install -r requirements.txt`
4. Create a PostgreSQL database
5. Create a .env file in the src directory with DATABASE_URL and FLASK_SECRET_KEY filled out.
   ```
   DATABASE_URL=postgresql://username:password@localhost/db_name
   FLASK_SECRET_KEY=secret_key
   ```
7. Apply the schema to the database you created with `psql -d db_name -f "schema.sql"` or another method.
8. Install FFmpeg and make sure that it's accessible through the terminal. Haven't tested this on other operating systems but on Windows placing the executable in the src directory is enough.
9. Start a local server with `flask run`
