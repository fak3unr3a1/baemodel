# Import the required modules
from flask import Flask, render_template, request, jsonify, session, redirect
import pymongo
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# MongoDB client initialization
client = pymongo.MongoClient("mongodb://localhost:27017/")  # Assuming MongoDB is running locally
db = client["your_database_name"]  # Replace "your_database_name" with your actual database name
users_collection = db["users"]  # Collection to store user credentials

# Route for user registration (Sign-up)
@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password

    # Check if the email is already registered
    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already registered'})

    # Insert the user into the database
    users_collection.insert_one({'email': email, 'password': hashed_password})
    
    # Set session variable to indicate user is logged in
    session['email'] = email
    
    # Redirect to home page
    return redirect('/home')

# Route for user login (Sign-in)
@app.route('/signin', methods=['POST'])
def signin():
    email = request.form['email']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password

    # Check if the user exists and the password is correct
    user = users_collection.find_one({'email': email, 'password': hashed_password})
    if user:
        # Set session variable to indicate user is logged in
        session['email'] = email
        # Redirect to home page
        return redirect('/home')
    else:
        return jsonify({'error': 'Invalid email or password'})

# Route for home page
@app.route('/home')
def home():
    # Check if the user is logged in
    if 'email' in session:
        return render_template('home.html')
    else:
        return redirect('/')  # Redirect to login page if not logged in

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove user's email from session
    return redirect('/')  # Redirect to login page

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
