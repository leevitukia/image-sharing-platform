# image-sharing-platform


### Features
- The user can create a new account or log in: Done
- The user can change their username and profile picture: Done
- Users can post & delete images: Done
- Users can search for other users: Done
- Users can favorite other users' pages: Done
- Users can attach a caption/description to their images: Done
- Users can comment on posts: Done
- Users can message other users: Done
- Users can like posts: Not implemented
- Good looking UI: absolutely not done

###  How to test the app (Tested on Ubuntu 24.04)
1. Clone the repo
2. Create and activate a Python 3.12 environment (3.10 works as well)
3. Install the required packages with `pip install -r requirements.txt`
4. Create a PostgreSQL database
5. Create a .env file in the src directory with DATABASE_URL and FLASK_SECRET_KEY filled out.
   ```
   DATABASE_URL=postgresql://username:password@localhost/db_name
   FLASK_SECRET_KEY=secret_key
   ```
7. Apply the schema to the database you created with `psql -d db_name -f "schema.sql"` or another method.
8. Install FFmpeg and make sure that it's accessible through the terminal. `sudo apt install ffmpeg`  (If you're using Windows make sure that it's accessible via PATH)
9. cd to the 'src' directory
10. Start a local server by running `python index.py`
