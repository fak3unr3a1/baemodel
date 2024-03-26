#server.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import subprocess
import re
# from aimodel import get_chat_response
# from intent import get_intent
from builder import understand_query_and_generate_list, perform_actions_and_get_results, execute_code, evaluate_results
from bae import chat_with_bae, identify_task, execute_task
import pymongo
import hashlib



from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# MongoDB client initialization
client = pymongo.MongoClient("mongodb+srv://UNR3A1:JXoO1X4EY6iArT0E@baemodelcluster.yvin3kv.mongodb.net/")
users_db = client["user_database"]  # Connecting to the "user_database" database
chat_history_db = client["chat_history"]  # Connecting to the "chat_history" database

# Collections
users_collection = users_db["users"]
user_db = client["user_database"] 
# Collections
users_collection = user_db["users"]

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



 


@app.route('/home')
def home():
    if 'email' not in session:
        return render_template('login.html')  # Render login page if user not logged in
    else:
        email = session['email']
        user = users_collection.find_one({'email': email})
        if user:
            if 'name' in user and 'ai_name' in user and user['name'] != '' and user['ai_name'] != '':
                # User has already provided name and AI name, render home_existing_user.html
                return render_template('home_existing_user.html', name=user['name'])
            else:
                # User needs to provide name and AI name
                return render_template('home_new_user.html')
        else:
            return render_template('login.html')  # Render login page if user not found

        
        
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
        # Render index.html for user interaction with AI
        return render_template('index.html')    
        


@app.route('/update_user_info', methods=['POST'])
def update_user_info():
    email = session['email']
    name = request.form['name']
    ai_name = request.form['ai_name']
    
    # Update user information in the database
    users_collection.update_one({'email': email}, {'$set': {'name': name, 'ai_name': ai_name}})
    
    return jsonify({'message': 'User information updated successfully'})




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
        return jsonify({'error': 'User not logged in'})

# Route to logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    return jsonify({'message': 'Logout successful'})

# Route to clear user data
@app.route('/clear_data', methods=['POST'])
def clear_data():
    if 'email' in session:
        email = session['email']
        # Clear user data from the database (implement as needed)
        return jsonify({'message': 'User data cleared successfully'})
    else:
        return jsonify({'error': 'User not logged in'})





@app.route('/tasks')
def tasks():
    return render_template('tasks.html')

@app.route('/build_task', methods=['POST'])
def build_task():
    if request.method == 'POST':
        query = request.form.get('builder_query')
        if query:
            try:
                # Generate a list of expected results from the user query
                expected_results = understand_query_and_generate_list(query)

                # Perform actions based on the expected results and get the actual results
                actions_results = perform_actions_and_get_results(expected_results)

                # Extract and execute the code snippet from the results
                code_snippet_match = re.search(r'```python\n(.+?)```', actions_results, re.DOTALL)
                if code_snippet_match:
                    code_snippet = code_snippet_match.group(1)
                    executed_output = execute_code(code_snippet)

                    # Evaluate the results and provide feedback
                    evaluation = evaluate_results(query, executed_output)
                    
                    return jsonify({'code_snippet': code_snippet, 'executed_output': executed_output, 'evaluation': evaluation})
                else:
                    return jsonify({'error': 'No code snippet found in the response.'})
            except Exception as e:
                return jsonify({'error': f'Error: {str(e)}'})
        else:
            return jsonify({'error': 'Builder query not provided.'})



@app.route('/submit_repo', methods=['POST'])
def submit_repo():
    if request.method == 'POST':
        repo_link = request.form.get('repo_link')
        folder_name = request.form.get('folder_name')  # Get the specified folder name
        task_description = request.form.get('task_description')  # Get the task description
        main_module_name = request.form.get('main_module_name')  # Get the main module name

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

                return 'Repository submitted successfully!'
            except Exception as e:
                return f'Error: {str(e)}'
        else:
            return 'Error: Repository link, folder name, task description, or main module name not provided.'

       

# from bae import task_name


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
                
                task_name = identify_task(user_input)
                if task_name:
                    # Execute the identified task
                    task_completion_message = execute_task(task_name)
                    # Provide feedback to the user
                    response_data = chat_with_bae(user_input, email)
                    assistant_response = response_data['assistant_response']
                    return jsonify({'response': assistant_response, 'task_completion_message': task_completion_message})
                else:
                    # No task identified, continue with regular chat interaction
                    response_data = chat_with_bae(user_input, email)
                    assistant_response = response_data['assistant_response']
                    return jsonify({'response': assistant_response})
            else:
                return jsonify({'error': 'User not logged in'})
        except Exception as e:
            return jsonify({'error': f'Error processing request: {str(e)}'})





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
                return jsonify({'task_executed': task_name})
            except Exception as e:
                return jsonify({'error': f'Error executing task: {str(e)}'})
        else:
            return jsonify({'error': 'Task not identified.'})

    

    
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




# Define the base directory for user tasks
base_directory = os.path.join(os.path.dirname(__file__), "usertasks")

@app.route('/get_user_tasks', methods=['GET'])
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

        return jsonify({'user_tasks': user_tasks})
    except Exception as e:
        return jsonify({'error': f'Error retrieving user tasks: {str(e)}'})



    
##example usage

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)