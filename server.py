#server.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import subprocess
import re
# from aimodel import get_chat_response
# from intent import get_intent
from bae import chat_with_bae, identify_task, execute_task
import pymongo
import hashlib
import datetime


from flask import Flask, render_template, request, jsonify, session, redirect
from pymongo import MongoClient
from flask_cors import CORS



  # Set a secret key for session management

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Fetch the MongoDB URI from the environment variable
mongodb_uri_srv = os.getenv("MONGODB_URI_SRV")



CORS(app)

try:

    # MongoDB client initialization
    client = pymongo.MongoClient(mongodb_uri_srv)
    users_db = client["user_database"]  # Connecting to the "user_database" database
    chat_history_db = client["chat_history"]  # Connecting to the "chat_history" database
    
    # Collections
    users_collection = users_db["users"]
    user_db = client["user_database"] 
    creators_collection = users_db["creators"] 
    users_collection = user_db["users"]
    
except pymongo.errors.ConnectionFailure as e:
    print("Error connecting to MongoDB Atlas:", e)



@app.route('/')
def login():
    if 'email' in session:
        return redirect('/home')  # Redirect to home page if user is already logged in
    else:
        return render_template('login.html')

@app.route('/signin', methods=['POST'])
def signin():
    email = request.form['email']
    password = request.form['password']
    
    # Hash the password for comparison
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    user = users_collection.find_one({'email': email, 'password': hashed_password})
    if user:
        session['email'] = email
        return redirect('/home')
    else:
        return jsonify({'error': 'Invalid email or password'})


@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']

    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already registered'})
    else:
        users_collection.insert_one({'email': email, 'password': hashed_password})
        session['email'] = email
        return redirect('/home')
    
    
    
@app.route('/user-data', methods=['POST'])
def get_user_data():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    print("Received email:", email)
    print("Received password:", password)
    
      
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    user = users_collection.find_one({'email': email, 'password': hashed_password})
    if user:
        session['email'] = email
        return jsonify({'success': 'Logged in successfully'})
    else:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    

from flask import render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

# MongoDB client initialization
users_db = client["user_database"]
creators_collection = users_db["creators"]

@app.route('/creator-login')
def creator_login():
    return render_template('creatorlogin.html')

@app.route('/creator-signin', methods=['POST'])
def creator_signin():
    email = request.form.get('email')
    password = request.form.get('password')

    creator = creators_collection.find_one({'email': email})

    if creator and check_password_hash(creator['password'], password):
        # Store creator's email in session for session management
        session['email'] = email
        return redirect(url_for('creatorshomepage'))
    else:
        # Handle invalid login credentials
        return jsonify({'error': 'Invalid email or password'})

@app.route('/creator-signup', methods=['POST'])
def creator_signup():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    country = request.form.get('country')
    address = request.form.get('address')
    password = request.form.get('password')

    # Hash the password before storing it
    hashed_password = generate_password_hash(password)

    # Check if the email is already registered
    if creators_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already registered'})
    else:
        # Insert the creator's details into the creators_collection
        creators_collection.insert_one({
            'name': name,
            'email': email,
            'phone': phone,
            'country': country,
            'address': address,
            'password': hashed_password
        })

        # Store creator's email in session for session management
        session['email'] = email
        return redirect(url_for('creatorshomepage'))


# Route for the creator's homepage
@app.route('/creatorshomepage')
def creatorshomepage():
    # Check if the user is logged in
    if 'email' not in session:
        return redirect(url_for('creator_login'))  # Redirect to creator login page if not logged in

    # Get the email from the session
    email = session['email']

    # Check if the email exists in the creators_collection
    creator = creators_collection.find_one({'email': email})

    if not creator:
        # If the email is not found in the collection, redirect to the login page
        return redirect(url_for('creator_login'))

    # If logged in and email exists in the collection, render the creatorshomepage.html template
    return render_template('creatorshomepage.html')


 


from flask import Flask, request, render_template, session




@app.route('/home')
def home():

        # Serve regular content for other users
        if 'email' not in session:
            return render_template('login.html')  # Render login page if user not logged in
        else:
            email = session['email']
            user = users_collection.find_one({'email': email})
            user_chat_collection = users_db[email]
            
            if user:
                if 'name' in user and 'ai_name' in user and user['name'] != '' and user['ai_name'] != '':
                    # User has already provided name and AI name, render home_existing_user.html
                    # Retrieve the conversation history from the database
                    conversation_history = list(user_chat_collection.find().sort("_id", 1))
                    return render_template('home_existing_user.html', name=user['name'], conversation_history=conversation_history, ai_name=user['ai_name'])
                else:
                    # User needs to provide name and AI name
                    return render_template('home_new_user.html')
            else:
                return render_template('login.html')  # Render login page if user not found


    
from bae import users_db, display_conversation_history 

# Route to display conversation history
@app.route('/conversation_history')
def conversation_history():
    try:
        # Check if the user is logged in
        if 'email' in session:
            email = session['email']

            # Determine the collection for the user's chat history based on their email
            user_chat_collection = users_db[email]
            user = users_collection.find_one({'email': email})


            # Retrieve the conversation history from the database
            conversation_history = list(user_chat_collection.find().sort("_id", 1))

            # Render the conversation history template with the retrieved data
            return render_template('conversation_history.html', conversation_history=conversation_history , ai_name=user['ai_name'])
        else:
            # If user is not logged in, redirect to login page
            return redirect(url_for('login'))
    except Exception as e:
        # Handle any errors that may occur
        return jsonify({'error': str(e)})
    




from bson import ObjectId
import json

@app.route('/conversation_history_react')
def conversation_history_react():
    try:
        if 'User-Email' in request.headers:
            email = request.headers['User-Email']

            user = users_collection.find_one({'email': email})
            user_chat_collection = users_db[email]
            
            if user:
                conversation_history = list(user_chat_collection.find().sort("_id", 1))
                # Convert ObjectId to string
                for message in conversation_history:
                    message['_id'] = str(message['_id'])
                # print('Conversation history:', conversation_history)
                
                return jsonify({'success': True, 'conversation_history': conversation_history}) # Return success flag along with conversation history
            else:
                return jsonify({'success': False, 'error': 'User not found'})
        else:
            return jsonify({'success': False, 'error': 'User email not provided'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500







        
        
@app.route('/save_user_info', methods=['POST'])
def save_user_info():
    email = session['email']
    name = request.form['name']
    ai_name = request.form['ai_name']
    
    # Update user information in the database
    users_collection.update_one({'email': email}, {'$set': {'name': name, 'ai_name': ai_name}})
    
    return redirect('/home')


@app.route('/index')
def index():
    if 'email' not in session:
        return render_template('login.html')  # Render login page if user not logged in
    else:
        email = session['email']
        user = users_collection.find_one({'email': email})
        if user:
            if 'name' in user:
                # User has provided name, render index.html with the user's name
                return render_template('index.html', name=user['name'], ai_name=user['ai_name'])
            else:
                # User has not provided name, render index.html without the name
                return render_template('index.html')
        else:
            return render_template('login.html')  # Render login page if user not found
   
        


@app.route('/update_user_info', methods=['POST'])
def update_user_info():
    email = session['email']
    name = request.form['name']
    ai_name = request.form['ai_name']
    
    # Update user information in the database
    users_collection.update_one({'email': email}, {'$set': {'name': name, 'ai_name': ai_name}})
    
    return jsonify({'message': 'User information updated successfully'})


from flask import request, jsonify
from pymongo import MongoClient
import os



####################################################################################################################################################

from flask import render_template, request, session, redirect, url_for

# Route for user settings
@app.route('/settings')
def settings():
    if 'email' not in session:
        return redirect(url_for('login'))  # Redirect to login page if user is not logged in

    # Retrieve user information from session
    email = session['email']
    user = users_collection.find_one({'email': email})
    if user:
        username = user.get('name', '')
        ai_name = user.get('ai_name', '')
        return render_template('settings.html', email=email, username=username, ai_name=ai_name)
    else:
        # User not found in database, redirect to login
        return redirect(url_for('login'))
    
    
from flask import jsonify, request

# Route for serving settings data to React
@app.route('/settings_data', methods=['GET', 'POST'])
def settings_data():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email not provided'})

        user = users_collection.find_one({'email': email})
        if user:
            username = user.get('name', '')
            ai_name = user.get('ai_name', '')
            return jsonify({'email': email, 'username': username, 'ai_name': ai_name})
        else:
            return jsonify({'error': 'User not found'})

    elif request.method == 'GET':
        email = request.args.get('email')

        if not email:
            return jsonify({'error': 'Email not provided'})

        user = users_collection.find_one({'email': email})
        if user:
            username = user.get('name', '')
            ai_name = user.get('ai_name', '')
            return jsonify({'email': email, 'username': username, 'ai_name': ai_name})
        else:
            return jsonify({'error': 'User not found'})

    else:
        return jsonify({'error': 'Method not allowed'}), 405




    
from flask import jsonify

# Route to update AI name
@app.route('/update_ai_name', methods=['POST'])
def update_ai_name():
    if 'email' in session:
        new_ai_name = request.form['new_ai_name']
        email = session['email']
        # Update AI name in the database
        users_collection.update_one({'email': email}, {'$set': {'ai_name': new_ai_name}})
        return jsonify({'message': 'AI name updated successfully'})
    else:
        return redirect(url_for('login'))

# Route to logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

# Route to clear user data
@app.route('/clear_data', methods=['POST'])
def clear_data():
    if 'email' in session:
        email = session['email']
        # Clear user data from the database (implement as needed)
        return jsonify({'message': 'User data cleared successfully'})
    else:
        return redirect(url_for('login'))
        





from flask import request, jsonify, session
import os

# Route to render tasks page
@app.route('/tasks')
def tasks():
    if 'email' not in session:
        return redirect(url_for('login'))  # Redirect to login page if user is not logged in

    # Retrieve user information from session
    email = session['email']
    user = users_collection.find_one({'email': email})
    if user:
        # Get the list of submitted tasks
        user_tasks = get_user_tasks()
        return render_template('tasks.html', ai_name=user['ai_name'], user_tasks=user_tasks)
    else:
        # User not found in database, redirect to login
        return redirect(url_for('login'))

from flask import request, jsonify, session
import os

@app.route('/submit_task', methods=['POST'])
def submit_task():
    if request.method == 'POST':
        user_input = request.form['user_input']
        main_module_name = request.form['main_module_name']  # Get the main module name from the form data
        task_name = identify_task(user_input)
        if task_name:
            try:
                # Execute the identified task with the specified main module name
                execute_task(task_name)

                # Get the user's email from the session
                email = session.get('email', '')

                # Store the user's email in a txt file
                with open('creatoremail.txt', 'a+') as file:
                    file.write(email + '\n')  # Append the email to the file with a newline character

                return jsonify({'task_executed': task_name})
            except Exception as e:
                return jsonify({'error': f'Error executing task: {str(e)}'})
        else:
            return jsonify({'error': 'Task not identified.'})


import uuid
import git

@app.route('/submit_repo', methods=['POST'])
def submit_repo():
    # Get the user's email from the session
    email = session.get('email')
    print("User's email:", email) # Add this line to output the received email to the console

    if request.method == 'POST':
        repo_link = request.form.get('repo_link')
        folder_name = request.form.get('folder_name')  # Get the specified folder name
        task_description = request.form.get('task_description')  # Get the task description
        main_module_name = request.form.get('main_module_name')  # Get the main module name
        email = session.get('email')  # Retrieve user's email from the session

        if repo_link and folder_name and task_description and main_module_name:
            try:
                # Clone the repository into the specified folder
                base_directory = os.path.join(os.path.dirname(__file__), "usertasks")
                target_folder = os.path.join(base_directory, folder_name)
                os.makedirs(target_folder, exist_ok=True)
                os.system(f'git clone {repo_link} {target_folder}')

                # Save the task description to a text file within the folder
                description_file_path = os.path.join(target_folder, 'task_description.txt')
                with open(description_file_path, 'w') as desc_file:
                    desc_file.write(task_description)

                # Save the main module name to a text file within the folder
                main_module_file_path = os.path.join(target_folder, 'main_module.txt')
                with open(main_module_file_path, 'w') as main_module_file:
                    main_module_file.write(main_module_name)
                    
                # Generate UUID for the task
                task_uuid = str(uuid.uuid4())

                # Save the UUID to a text file within the folder
                uuid_file_path = os.path.join(target_folder, 'task_uuid.txt')
                with open(uuid_file_path, 'w') as uuid_file:
                    uuid_file.write(task_uuid)

                # Define the path to the creator email file
                creator_email_file_path = os.path.join(target_folder, 'creatoremail.txt')

                # Store the user's email in a txt file inside the task folder
                with open(creator_email_file_path, 'a+') as file:
                    file.write(email + '\n')  # Append the email to the file with a newline character

                # Redirect to tasks page after submission
                return jsonify({'message': 'Repository submitted successfully!', 'task_uuid': task_uuid})
            except Exception as e:
                return jsonify({'error': f'Error: {str(e)}'})
        else:
            return jsonify({'error': 'Repository link, folder name, task description, or main module name not provided.'})

        
        
@app.route('/submit_installation', methods=['POST'])
def submit_installation():
    if request.method == 'POST':
        installation_command = request.form.get('installation_command')
        if installation_command:
            try:
                subprocess.run(installation_command, shell=True, check=True)
                # Installation successful
                return 'Installation Successful'
            except subprocess.CalledProcessError as e:
                # Installation failed, return error message
                return f'Installation Failed: {e.stderr.decode()}'
        else:
            return 'Error: Installation command not provided.'
        
        
        
        
        

from flask import request

@app.route('/save_uuid', methods=['POST'])
def save_uuid():
    folder_name = request.form.get('folder_name')
    task_uuid = request.form.get('task_uuid')
    if folder_name and task_uuid:
        try:
            # Define the path to the folder and the UUID file
            folder_path = os.path.join(os.path.dirname(__file__), "usertasks", folder_name)
            uuid_file_path = os.path.join(folder_path, 'task_uuid.txt')

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Save the UUID to the file
            with open(uuid_file_path, 'w') as uuid_file:
                uuid_file.write(task_uuid)

            return 'UUID saved successfully'
        except Exception as e:
            return f'Error saving UUID: {str(e)}'
    else:
        return 'Error: Folder name or task UUID not provided.'



        
        
# Import necessary modules
from flask import request, jsonify, session

from flask import jsonify

import shutil
import os
from bae import is_task_enabled
# Route to enable a task for a user
@app.route('/enable_task', methods=['POST'])
def enable_task_route():
    if 'email' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'})

    # Retrieve the task UUID from the request
    task_uuid = request.json.get('task_uuid')
    if not task_uuid:
        return jsonify({'success': False, 'error': 'Task UUID not provided'})

    # Get the path of the folder in usertasks corresponding to the UUID
    usertasks_folder = os.path.join(os.path.dirname(__file__), 'usertasks')
    
    # Iterate over every folder inside usertasks to find the matching UUID
    for folder_name in os.listdir(usertasks_folder):
        folder_path = os.path.join(usertasks_folder, folder_name)
        uuid_file_path = os.path.join(folder_path, 'task_uuid.txt')

        # Check if the folder contains the task_uuid.txt file
        if os.path.exists(uuid_file_path):
            # Read the UUID from the file
            with open(uuid_file_path, 'r') as uuid_file:
                folder_uuid = uuid_file.read().strip()

            # Check if the UUID matches the one from the client
            if folder_uuid == task_uuid:
                # Get the user's email from the session
                user_email = session['email']
                
                # Check if the task is already enabled for the user
                if is_task_enabled(user_email, folder_name):
                    return jsonify({'success': False, 'error': 'Task already enabled for the user'})
                
                # Create a directory for the user if it doesn't exist
                user_enabled_tasks_folder = os.path.join(os.path.dirname(__file__), 'enabledtasks', user_email)
                if not os.path.exists(user_enabled_tasks_folder):
                    os.makedirs(user_enabled_tasks_folder)

                # Copy the folder to the user's directory in enabledtasks
                enabled_task_folder = os.path.join(user_enabled_tasks_folder, folder_name)

                try:
                    shutil.copytree(folder_path, enabled_task_folder)
                    return jsonify({'success': True})
                except Exception as e:
                    print("Error enabling task:", e)
                    return jsonify({'success': False, 'error': 'Error enabling task'})

    # If no matching UUID is found
    return jsonify({'success': False, 'error': 'Task folder not found'})


from flask import Flask
from flask_cors import CORS
from flask import request, jsonify
CORS(app)
@app.route('/enable_task_react', methods=['POST'])
def enable_task_react_route():
    # Retrieve the email from the request headers
    email = request.headers.get('User-Email')
    if not email:
        return jsonify({'success': False, 'error': 'User email not provided'})

    # Retrieve the task UUID from the request
    task_uuid = request.json.get('task_uuid')
    if not task_uuid:
        return jsonify({'success': False, 'error': 'Task UUID not provided'})

    # Get the path of the folder in usertasks corresponding to the UUID
    usertasks_folder = os.path.join(os.path.dirname(__file__), 'usertasks')

    # Iterate over every folder inside usertasks to find the matching UUID
    for folder_name in os.listdir(usertasks_folder):
        folder_path = os.path.join(usertasks_folder, folder_name)
        uuid_file_path = os.path.join(folder_path, 'task_uuid.txt')

        # Check if the folder contains the task_uuid.txt file
        if os.path.exists(uuid_file_path):
            # Read the UUID from the file
            with open(uuid_file_path, 'r') as uuid_file:
                folder_uuid = uuid_file.read().strip()

            # Check if the UUID matches the one from the client
            if folder_uuid == task_uuid:
                # Check if the task is already enabled for the user
                if is_task_enabled(email, folder_name):
                    return jsonify({'success': False, 'error': 'Task already enabled for the user'})

                # Create a directory for the user if it doesn't exist
                user_enabled_tasks_folder = os.path.join(os.path.dirname(__file__), 'enabledtasks', email)
                if not os.path.exists(user_enabled_tasks_folder):
                    os.makedirs(user_enabled_tasks_folder)

                # Copy the folder to the user's directory in enabledtasks
                enabled_task_folder = os.path.join(user_enabled_tasks_folder, folder_name)

                try:
                    shutil.copytree(folder_path, enabled_task_folder)
                    return jsonify({'success': True})
                except Exception as e:
                    print("Error enabling task:", e)
                    return jsonify({'success': False, 'error': 'Error enabling task'})

    # If no matching UUID is found
    return jsonify({'success': False, 'error': 'Task folder not found'})


import os
import shutil
from flask import request, jsonify, session
from bae import is_task_enabled



import os
import shutil
import stat  # Import the stat module to handle file attributes

def remove_readonly(func, path, _):
    """Clear the read-only bit and reattempt the operation"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def remove_task_by_name(email, task_name):
    try:
        # Get the path of the user's directory
        user_directory = os.path.join(os.path.dirname(__file__), 'enabledtasks', email)

        print(f"Checking for task folder in: {user_directory}")

        # Check if the user's directory exists
        if os.path.exists(user_directory):
            print(f"User's directory exists.")

            # Iterate over each folder in the user's directory
            for folder_name in os.listdir(user_directory):
                folder_path = os.path.join(user_directory, folder_name)
                uuid_file_path = os.path.join(folder_path, 'task_uuid.txt')

                # Check if the folder contains the task_uuid.txt file
                if os.path.exists(uuid_file_path):
                    # Read the UUID from the file
                    with open(uuid_file_path, 'r') as uuid_file:
                        folder_uuid = uuid_file.read().strip()

                    # Check if the folder UUID matches the provided task name
                    if folder_uuid == task_name:
                        print(f"Match found for task UUID: {task_name} in folder: {folder_path}")

                        # Attempt to remove the task folder and its contents
                        try:
                            # Remove read-only attribute before attempting to delete
                            shutil.rmtree(folder_path, onerror=remove_readonly)
                            return True, None  # Success, no error message
                        except Exception as e:
                            return False, f"Error removing task folder: {e}"

            # If no matching task UUID is found
            return False, f"Task '{task_name}' does not exist."
        else:
            return False, f"User's directory does not exist."
    except Exception as e:
        return False, f'Error removing task: {e}'


def move_task_to_deleted(email, task_name):
    try:
        # Get the path of the task folder
        task_folder = os.path.join(os.path.dirname(__file__), 'enabledtasks', email, task_name)

        print(f"Checking for task folder in: {task_folder}")

        # Check if the task folder exists
        if os.path.exists(task_folder):
            print(f"Task folder exists.")

            # Move the task folder to the DeletedTasks directory
            deleted_tasks_folder = os.path.join(os.path.dirname(__file__), 'DeletedTasks')
            if not os.path.exists(deleted_tasks_folder):
                os.makedirs(deleted_tasks_folder)  # Create the DeletedTasks directory if it doesn't exist

            # Move the task folder to DeletedTasks
            shutil.move(task_folder, os.path.join(deleted_tasks_folder, task_name))

            return True, None  # Success, no error message
        else:
            return False, f"Task '{task_name}' does not exist."
    except Exception as e:
        return False, f'Error moving task to DeletedTasks: {e}'


from bae import is_task_enabled

import os

@app.route('/remove_user_task', methods=['POST'])
def remove_user_task():
    if 'email' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'})

    # Retrieve the task name and UUID from the request
    task_data = request.json
    task_name = task_data.get('task_name')
    if not task_name:
        return jsonify({'success': False, 'error': 'Task name not provided'})

    print(f"Received task name: {task_name}")

    # Call the function to remove the task
    success, error_msg = remove_task_by_name(session['email'], task_name)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': error_msg})

    
    
    
# from flask import session, request, jsonify
# # Function to check if a task is enabled for a user
# @app.route('/get_response', methods=['POST'])
# def get_response():
#     if request.method == 'POST':
#         user_input = request.form['user_input']
#         try:
#             # Check if the user is logged in
#             if 'email' in session:
#                 email = session['email']
                
#                 # Determine the collection for the user's chat history based on their email
#                 user_chat_collection = users_db[email]
                
#                 task_identifier = identify_task(user_input)
#                 if task_identifier:
#                     # Check if the task is enabled for the user
#                     user_document = users_collection.find_one({'email': email})
#                     if user_document and 'enabled_tasks' in user_document and task_identifier in user_document['enabled_tasks']:
#                         # Task is enabled, execute it
#               is_task_enabled          execute_task(task_identifier, user_input, email)
                        
#                         # Notify the user that the task has been executed successfully
#                         return jsonify({'Success': 'Task executed successfully.'})
#                     else:
#                         # Task is not enabled for the user
#                         return jsonify({'error': 'Task is not enabled. Please enable it from the store.'})
#                 else:
#                     # No task identified, continue with regular chat interaction
#                     response_data = chat_with_bae(user_input, email)
#                     assistant_response = response_data['assistant_response']
                    
#                     return jsonify({'response': assistant_response})
#             else:
#                 return jsonify({'error': 'User not logged in'})
#         except Exception as e:
#             return jsonify({'error': f'Error processing request: {str(e)}'})

# from bae import task_name



from flask import session

@app.route('/get_response', methods=['POST'])
def get_response():
    if request.method == 'POST':
        user_input = request.form['user_input']
        try:
            # Check if the user is logged in
            if 'email' in session:
                email = session['email']
                
                # Determine the collection for the user's chat history based on their email
                user_chat_collection = users_db[email]
                
                task_name = identify_task(user_input, user_email=email)
                if task_name:
                    # Execute the identified task with the user input as query
                    execution_result = execute_task(task_name, query=user_input, user_email=email)
                    if 'error_message' in execution_result:
                        return jsonify({'error': execution_result['error_message']})
                    else:
                        result_dest_path = execution_result
                    
                    # Provide feedback to the user
                    response_data = chat_with_bae(user_input, email)
                    assistant_response = response_data['assistant_response']
                    
                    # Save the data to session
                    session['response'] = {'assistant_response': assistant_response}
                    
                    return jsonify({'response': assistant_response, 'result_dest_path': result_dest_path})
                else:
                    # No task identified, continue with regular chat interaction
                    response_data = chat_with_bae(user_input, email)
                    assistant_response = response_data['assistant_response']
                    
                    return jsonify({'response': assistant_response})
            else:
                return jsonify({'error': 'User not logged in'})
        except Exception as e:
            return jsonify({'error': f'Error processing request: {str(e)}'})



from flask import Flask, request, jsonify, session
from flask_cors import CORS


CORS(app)  # Enable CORS for your Flask app

@app.route('/get_response_react', methods=['POST'])
def get_response_react():
    if request.method == 'POST':
        try:
            data = request.get_json()  # Parse JSON data from request body
            user_input = data.get('user_input')

            if not user_input:
                return jsonify({'error': 'User input not provided'})

            email = request.headers.get('User-Email')
            if not email:
                return jsonify({'error': 'User email not provided'})

            user_chat_collection = users_db[email]

            task_name = identify_task(user_input, user_email=email)
            if task_name:
                execution_result = execute_task(task_name, query=user_input, user_email=email)
                if 'error_message' in execution_result:
                    return jsonify({'error': execution_result['error_message']})
                else:
                    result_dest_path = execution_result

                response_data = chat_with_bae(user_input, email)
                assistant_response = response_data['assistant_response']

                session['response'] = {'assistant_response': assistant_response}

                return jsonify({'response': assistant_response, 'result_dest_path': result_dest_path})
            else:
                response_data = chat_with_bae(user_input, email)
                assistant_response = response_data['assistant_response']

                return jsonify({'response': assistant_response})

        except Exception as e:
            return jsonify({'error': f'Error processing request: {str(e)}'})








import os

# Define the base directory for user tasks
base_directory = os.path.join(os.path.dirname(__file__), "enabledtasks")

@app.route('/get_user_tasks', methods=['GET'])
def get_user_tasks():
    try:
        user_tasks = []
        
        # Retrieve the user's email from the query parameters
        user_email = request.args.get('email')
        if not user_email:
            return {'error': 'User email not provided'}

        # Construct the user's task directory path based on their email
        user_task_directory = os.path.join(base_directory, user_email)
        
        # Check if the user's task directory exists
        if not os.path.exists(user_task_directory):
            return {'error': 'User task directory not found'}
        
        # Iterate through each task folder in the user's directory
        for task_folder in os.listdir(user_task_directory):
            task_path = os.path.join(user_task_directory, task_folder)
            if os.path.isdir(task_path):
                # Check if the task folder contains a task_description.txt file
                description_file = os.path.join(task_path, 'task_description.txt')
                if os.path.exists(description_file):
                    # Read the task description from the file
                    with open(description_file, 'r') as f:
                        task_description = f.read()
                else:
                    task_description = "No description available"

                # Append the task name and description to the user_tasks list
                user_tasks.append({'name': task_folder, 'description': task_description})

        return user_tasks
    except Exception as e:
        return {'error': str(e)}



    
from bae import remove_task 
#from entire store
@app.route('/remove_task', methods=['POST'])
def remove_task_route():
    if request.method == 'POST':
        task_name = request.form['task_name']  # Get the task name from the request
        if task_name:
            try:
                # Call the remove_task function to delete the specified task
                result_message = remove_task(task_name)
                return jsonify({'message': result_message})  # Return the result message from remove_task
            except Exception as e:
                return jsonify({'error': f'Error removing task "{task_name}": {str(e)}'})
        else:
            return jsonify({'error': 'Task name not provided.'})



@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

# Define route to serve the creator documentation page
@app.route('/documentation')
def documentation():
    return render_template('creatordocumentation.html')

from flask import request, jsonify

from flask import session, request, jsonify

from pymongo import MongoClient




# Route to render store page and display submitted tasks

import os

@app.route('/store')
def store():
    if 'email' not in session:
        return redirect(url_for('login'))  # Redirect to login page if user is not logged in

    # Retrieve list of folders inside usertasks directory
    base_directory = os.path.join(os.path.dirname(__file__), "usertasks")
    folders = [f for f in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, f))]

    # Create a list to store folder details (name, description, uuid)
    folder_details = []

    # Iterate over each folder to retrieve description and uuid
    for folder in folders:
        folder_path = os.path.join(base_directory, folder)
        description_file_path = os.path.join(folder_path, 'task_description.txt')
        uuid_file_path = os.path.join(folder_path, 'task_uuid.txt')
        description = ''  # Default value if description file is not found
        uuid = ''  # Default value if uuid file is not found

        # Read description from task_description.txt if file exists
        if os.path.exists(description_file_path):
            with open(description_file_path, 'r') as desc_file:
                description = desc_file.read()

        # Read uuid from task_uuid.txt if file exists
        if os.path.exists(uuid_file_path):
            with open(uuid_file_path, 'r') as uuid_file:
                uuid = uuid_file.read()

        # Append folder details to the list
        folder_details.append({'name': folder, 'description': description, 'uuid': uuid})

    # Pass folders list and folder details to the template along with the task UUIDs
    return render_template('store.html', folders=folder_details, task_uuids=[folder['uuid'] for folder in folder_details])

import os
from flask import jsonify

CORS(app, supports_credentials=True)

@app.route('/store-react-native')
def store_react_native():
    # if 'email' not in session:
    #     return jsonify({'error': 'User not logged in'})  # Return an error if user is not logged in

    base_directory = os.path.join(os.path.dirname(__file__), "usertasks")
    folders = [f for f in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, f))]

    folder_details = []

    for folder in folders:
        folder_path = os.path.join(base_directory, folder)
        description_file_path = os.path.join(folder_path, 'task_description.txt')
        uuid_file_path = os.path.join(folder_path, 'task_uuid.txt')
        description = ''  # Default value if description file is not found
        uuid = ''  # Default value if uuid file is not found

        if os.path.exists(description_file_path):
            with open(description_file_path, 'r') as desc_file:
                description = desc_file.read()

        if os.path.exists(uuid_file_path):
            with open(uuid_file_path, 'r') as uuid_file:
                uuid = uuid_file.read()

        folder_details.append({'name': folder, 'description': description, 'uuid': uuid})

    return jsonify({'folders': folder_details})


# Helper function to retrieve user tasks
def get_user_tasks():
    try:
        user_tasks = []

        # Iterate through each task folder in the base directory
        for task_folder in os.listdir(base_directory):
            task_path = os.path.join(base_directory, task_folder)
            if os.path.isdir(task_path):
                # Check if the task folder contains a task_description.txt file
                description_file = os.path.join(task_path, 'task_description.txt')
                if os.path.exists(description_file):
                    # Read the task description from the file
                    with open(description_file, 'r') as f:
                        task_description = f.read()
                else:
                    task_description = "No description available"

                # Append the task name and description to the user_tasks list
                user_tasks.append({'name': task_folder, 'description': task_description})

        return user_tasks
    except Exception as e:
        return []



from flask import Flask, request, jsonify
import os

# import speech_recognition as sr



# # Function for TTS
# def speak(text):
#     voice = "en-GB-RyanNeural"
#     output_file = "output.mp3"
#     command = f'edge-tts --voice "{voice}" --text "{text}" --write-media "{output_file}"'
#     os.system(command)

#     pygame.init()
#     pygame.mixer.init()

#     try:
#         pygame.mixer.music.load(output_file)
#         pygame.mixer.music.play()
#         while pygame.mixer.music.get_busy():
#             pygame.time.Clock().tick(10)
#     except Exception as e:
#         print(e)
#     finally:
#         pygame.mixer.music.stop()
#         pygame.mixer.quit()

# # Function for STT
# def get_user_response():
#     r = sr.Recognizer()
#     with sr.Microphone() as source:
#         print("Listening for response...")
#         r.adjust_for_ambient_noise(source)
#         audio = r.listen(source)
#     try:
#         response = r.recognize_google(audio, language='en-us').lower()
#         return response
#     except sr.UnknownValueError:
#         return "Could not understand audio"
#     except sr.RequestError as e:
#         return f"Error with the speech recognition service: {e}"

# @app.route('/tts', methods=['POST'])
# def tts():
#     text = request.json['text']
#     speak(text)
#     return jsonify({'message': 'TTS completed'})

# @app.route('/stt', methods=['GET'])
# def stt():
#     response = get_user_response()
#     return jsonify({'response': response})





# Import necessary modules
from flask import request, jsonify, session

# Route to handle AI functionalities
@app.route('/ai-functionality', methods=['POST'])
def ai_functionality():
    # Check if the request method is POST
    if request.method == 'POST':
        # Get the functionality type from the request data
        functionality_type = request.json.get('functionality_type')

        # Determine the action based on the functionality type
        if functionality_type == 'chat_with_bae':
            # Extract necessary data from the request
            user_input = request.json.get('user_input')
            email = session.get('email')

            # Call the appropriate function to handle the chat functionality
            response_data = chat_with_bae(user_input, email)

            # Return the response data as JSON
            return jsonify(response_data)
        elif functionality_type == 'identify_task':
            # Extract necessary data from the request
            user_input = request.json.get('user_input')

            # Call the appropriate function to identify the task
            task_name = identify_task(user_input)

            # Return the identified task name as JSON
            return jsonify({'task_name': task_name})
        elif functionality_type == 'execute_task':
            # Extract necessary data from the request
            task_name = request.json.get('task_name')
            email = session.get('email')

            # Call the appropriate function to execute the task
            execution_result = execute_task(task_name, email)

            # Return the execution result as JSON
            return jsonify(execution_result)
        else:
            # If the functionality type is not recognized, return an error response
            return jsonify({'error': 'Invalid functionality type'})
    else:
        # If the request method is not POST, return an error response
        return jsonify({'error': 'Only POST requests are allowed for this endpoint'})

# Import necessary libraries
from flask import Flask, request, jsonify
import pymongo

# Connect to MongoDB Atlas
try:
    client = pymongo.MongoClient("mongodb+srv://UNR3A1:JXoO1X4EY6iArT0E@baemodelcluster.yvin3kv.mongodb.net/")
    usertextfiles_db = client["usertextfiles"]  # Connecting to the "usertextfiles" database
except pymongo.errors.ConnectionFailure as e:
    print("Failed to connect to MongoDB Atlas:", e)


from datetime import datetime

# Endpoint to store text data in MongoDB
@app.route('/api/store-text-data', methods=['POST'])
def store_text_data():
    try:
        user_email = request.headers.get('User-Email')  # Extract the user's email from request headers
        print('User Email:', user_email)
        if not user_email:
            return jsonify({'error': 'User email not provided'}), 400
        print('Received request to store text data...')
        data = request.json  # Get the data from the request body
        print('Received data:', data)
        text = data.get('text')  # Extract the text from the data

        print('Text:', text)
        print('User Email:', user_email)
        timestamp = datetime.now()  # Generate current timestamp
        user_collection = usertextfiles_db[user_email]  # Get the collection for the user's email
        user_collection.insert_one({'text': text, 'timestamp': timestamp})  # Insert the text data with timestamp
        return jsonify({'message': 'Text data stored successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500






# Endpoint to retrieve stored text data from MongoDB
@app.route('/api/get-stored-text-data', methods=['GET'])
def get_stored_text_data():
    try:
        user_email = request.headers.get('User-Email')  # Extract the user's email from request headers
        if not user_email:
            return jsonify({'error': 'User email not provided'}), 400
        stored_data = list(usertextfiles_db[user_email].find())  # Retrieve all stored text data for the user
        # Convert ObjectId to string
        for data in stored_data:
            data['_id'] = str(data['_id'])
        return jsonify({'storedData': stored_data}), 200  # Include the timestamp along with the text data
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Endpoint to update stored text data in MongoDB
@app.route('/api/update-stored-text', methods=['POST'])
def update_stored_text():
    try:
        print('Received request to update stored text...')
        data = request.json  # Get the data from the request body
        print('Received data:', data)
        text = data.get('text')  # Extract the text from the data
        user_email = request.headers.get('User-Email')  # Extract the user's email from request headers
        if not user_email:
            return jsonify({'error': 'User email not provided'}), 400
        print('Text:', text)
        print('User Email:', user_email)
        
        # Update the stored text data for the user in MongoDB
        usertextfiles_db[user_email].update_one({}, {'$set': {'text': text}})
        
        return jsonify({'message': 'Text data updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



    
    
    
##example usage

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
