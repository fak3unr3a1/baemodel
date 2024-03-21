#server.py

from flask import Flask, render_template, request, jsonify
import os
import subprocess
import re
# from aimodel import get_chat_response
# from intent import get_intent
from builder import understand_query_and_generate_list, perform_actions_and_get_results, execute_code, evaluate_results
from bae import chat_with_bae, identify_task, execute_task

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

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
        if repo_link and folder_name and task_description:
            try:
                # Clone the repository into the specified folder
                base_directory = r'C:\Users\cglyn\BAE4\B.A.E\usertasks'
                target_folder = os.path.join(base_directory, folder_name)
                os.makedirs(target_folder, exist_ok=True)
                os.system(f'git clone {repo_link} {target_folder}')

                # Save the task description to a text file within the folder
                description_file_path = os.path.join(target_folder, 'task_description.txt')
                with open(description_file_path, 'w') as desc_file:
                    desc_file.write(task_description)

                return 'Repository submitted successfully!'
            except Exception as e:
                return f'Error: {str(e)}'
        else:
            return 'Error: Repository link, folder name, or task description not provided.'





@app.route('/get_response', methods=['POST'])
def get_response():
    if request.method == 'POST':
        user_input = request.form['user_input']
        try:
            # Call the chat_with_bae function to get the AI response
            response_data = chat_with_bae(user_input)
            
            # Check if the response contains an error
            if 'error' in response_data:
                return jsonify({'error': response_data['error']})

            # Get the assistant's response from the data
            assistant_response = response_data['assistant_response']
            
            # Return the assistant's response
            return jsonify({'response': assistant_response})
        except Exception as e:
            return jsonify({'error': f'Error processing request: {str(e)}'})









@app.route('/submit_task', methods=['POST'])
def submit_task():
    if request.method == 'POST':
        user_input = request.form['user_input']
        task_name = identify_task(user_input)
        if task_name:
            try:
                # Execute the identified task
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






@app.route('/get_user_tasks', methods=['GET'])
def get_user_tasks():
    try:
        user_tasks_folder = r'C:\Users\cglyn\BAE4\B.A.E\usertasks'
        user_tasks = []

        # Iterate through each task folder
        for task_folder in os.listdir(user_tasks_folder):
            task_path = os.path.join(user_tasks_folder, task_folder)
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
