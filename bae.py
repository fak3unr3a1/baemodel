#bae.py



import os
import spacy
import pymongo
import g4f
from difflib import SequenceMatcher
import logging
import mimetypes

# Configure logging
logging.basicConfig(filename='bae.log', level=logging.ERROR)

# Load the English language model for spaCy
nlp = spacy.load("en_core_web_sm")

# Connect to MongoDB Atlas
try:
    client = pymongo.MongoClient("mongodb+srv://UNR3A1:JXoO1X4EY6iArT0E@baemodelcluster.yvin3kv.mongodb.net/")
    db = client["chat_history"]  # Connecting to the "chat_history" database
    users_db = client["user_database"]  # Connecting to the "user_database" database
except pymongo.errors.ConnectionFailure as e:
    print("Failed to connect to MongoDB Atlas:", e)
    logging.error("Failed to connect to MongoDB Atlas: %s", e)
    
    
    
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()



import os

# Define function to enable a task for a user
def enable_task(user_email, task_name):
    try:
        # Check if the task is already enabled for the user
        if is_task_enabled(user_email, task_name):
            return False, 'Task already enabled for the user.'
        
        # Retrieve the task UUID from the task folder
        task_folder = os.path.join(os.path.dirname(__file__), "usertasks", task_name)
        uuid_file_path = os.path.join(task_folder, "task_uuid.txt")
        with open(uuid_file_path, 'r') as uuid_file:
            task_uuid = uuid_file.read().strip()
        
        # Update the user's document in the users collection to mark the task as enabled
        users_db.users.update_one({'email': user_email}, {'$addToSet': {'enabled_tasks': {'name': task_name, 'uuid': task_uuid}}})
        return True, 'Task enabled successfully.'
    except Exception as e:
        print("Error enabling task:", e)
        logging.error("Error enabling task: %s", e)
        return False, f'Error enabling task: {e}'


# Define function to check if a task is enabled for a user
def is_task_enabled(user_email, task_name):
    # Check if the task folder exists in the user's enabled tasks folder
    user_enabled_tasks_folder = os.path.join(os.path.dirname(__file__), "enabledtasks", user_email)
    task_folder = os.path.join(user_enabled_tasks_folder, task_name)
    return os.path.exists(task_folder)



import os
import sys
import importlib.util
import shutil

# Modify execute_task function to check task enablement
def execute_task(task_name, query=None, user_email=None):
    if user_email and not is_task_enabled(user_email, task_name):
        error_message = 'Task is not enabled for the user.'
        print(error_message)
        return {'output_type': 'error', 'error_message': error_message}
    result_dest_path = None
    try:
        # Get the directory path for the user's enabled tasks
        user_enabled_tasks_folder = os.path.join(os.path.dirname(__file__), "enabledtasks", user_email)
        
        # Check if the task folder exists for the user
        if not os.path.exists(user_enabled_tasks_folder):
            error_message = f'Enabled tasks folder not found for user {user_email}.'
            print(error_message)
            return {'output_type': 'error', 'error_message': error_message}
        
        # Get the main module name from the main_module.txt file
        main_module_file = os.path.join(user_enabled_tasks_folder, task_name, "main_module.txt")
        with open(main_module_file, 'r') as f:
            main_module_name = f.read().strip()
        
        # Add the task folder to the Python path
        task_folder = os.path.join(user_enabled_tasks_folder, task_name)
        sys.path.append(task_folder)
        
        # Load the main module
        filename = os.path.join(task_folder, main_module_name)
        spec = importlib.util.spec_from_file_location(main_module_name, filename)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)        

        # Execute the main function of the task
        if query is not None and hasattr(main_module, 'main') and callable(main_module.main):
            result = main_module.main(query)
        else:
            result = main_module.main()
        
        # Create a folder to store executed tasks if it doesn't exist
        executed_tasks_folder = os.path.join(os.path.dirname(__file__), "executed_tasks")
        os.makedirs(executed_tasks_folder, exist_ok=True)
        
        # Move the result file to the executed tasks folder
        if result:
            result_file_name = os.path.basename(result)
            result_dest_path = os.path.join(executed_tasks_folder, result_file_name)
            
            if os.path.exists(result_dest_path):
                print("File already exists in the destination folder. Renaming...")
                result_file_name = "new_" + result_file_name
                result_dest_path = os.path.join(executed_tasks_folder, result_file_name)
            
            shutil.move(result, result_dest_path)
            print("File moved successfully to:", result_dest_path)
        
        return result_dest_path
        
    except FileNotFoundError as e:
        error_message = f'Task file not found: {e}'
        print("Error:", error_message)
        return {'output_type': 'error', 'error_message': error_message}
    except Exception as e:
        error_message = f'Error executing task: {e}'
        print("Error:", error_message)
        return {'output_type': 'error', 'error_message': error_message}


# def execute_task(task_name, query=None):
#     result_dest_path = None  # Initialize result_dest_path to None
    
#     try:
#         project_folder = os.path.join(os.path.dirname(__file__), "usertasks", task_name)
        
#         # Read the main module name from main_module.txt
#         main_module_file = os.path.join(project_folder, "main_module.txt")
#         with open(main_module_file, 'r') as f:
#             main_module_name = f.read().strip()  # Read the main module name and remove any leading/trailing whitespace
        
#         # Add the project folder to sys.path to allow importing modules from it
#         sys.path.append(project_folder)
        
#         filename = os.path.join(project_folder, f"{main_module_name}")

#         # Dynamically import the main module
#         spec = importlib.util.spec_from_file_location(main_module_name, filename)
#         main_module = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(main_module)        
        
#         # Execute the main function within the dynamically imported module
#         if query is not None and hasattr(main_module, 'main') and callable(main_module.main):
#             result = main_module.main(query)  # Pass the query to the main function if it requires it
#         else:
#             result = main_module.main()  # Call the main function without passing any arguments
        
#         # Create a folder for executed tasks if it doesn't exist
#         executed_tasks_folder = os.path.join(os.path.dirname(__file__), "executed_tasks")
#         os.makedirs(executed_tasks_folder, exist_ok=True)
        
#         # Move the result to the executed tasks folder
#         if result:
#             # Assuming result is a file path
#             result_file_name = os.path.basename(result)
#             result_dest_path = os.path.join(executed_tasks_folder, result_file_name)
            
#             # Handle existing files
#             if os.path.exists(result_dest_path):
#                 print("File already exists in the destination folder. Renaming...")
#                 result_file_name = "new_" + result_file_name
#                 result_dest_path = os.path.join(executed_tasks_folder, result_file_name)
            
#             shutil.move(result, result_dest_path)
#             print("File moved successfully to:", result_dest_path)  # Print the destination path for debugging
        
#         # Return the path where the result is saved
#         return result_dest_path
        
#     except FileNotFoundError as e:
#         print("Task file not found:", e)
#         logging.error("Task file not found: %s", e)
#         return {'output_type': 'error', 'error_message': f'Task file not found: {e}'}
#     except Exception as e:
#         print("Error executing task:", e)
#         logging.error("Error executing task: %s", e)
#         return {'output_type': 'error', 'error_message': f'Error executing task: {e}'}



import os
import logging

# Modify identify_task function to consider only enabled tasks
def identify_task(query, user_email=None):
    try:
        project_folder = os.path.join(os.path.dirname(__file__), "enabledtasks", user_email)
        query_keywords = set(token.text for token in nlp(query) if not token.is_stop)
        best_match_folder = None
        best_match_score = 0.0

        for folder_name in os.listdir(project_folder):
            folder_path = os.path.join(project_folder, folder_name)
            if os.path.isdir(folder_path):
                description_file = os.path.join(folder_path, 'task_description.txt')
                if os.path.exists(description_file):
                    with open(description_file, 'r') as desc_file:
                        description = desc_file.read()
                    desc_doc = nlp(description)
                    desc_keywords = set(token.text for token in desc_doc if not token.is_stop)
                    score = len(query_keywords.intersection(desc_keywords)) / len(query_keywords.union(desc_keywords))
                    if score > best_match_score:
                        best_match_folder = folder_name
                        best_match_score = score

        return best_match_folder
    except Exception as e:
        print("Error identifying task:", e)
        logging.error("Error identifying task: %s", e)
        return None





import os
import shutil
import stat

def remove_task(task_name):
    try:
        # Construct path to the task folder
        task_folder = os.path.join(os.path.dirname(__file__), "usertasks", task_name)
        
        # Check if the task folder exists
        if os.path.exists(task_folder):
            # Iterate through each file and directory within the task folder
            for root, dirs, files in os.walk(task_folder, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    os.chmod(file_path, stat.S_IWRITE)  # Set file permissions to allow deletion
                    os.remove(file_path)  # Remove the file
                
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    os.chmod(dir_path, stat.S_IWRITE)  # Set directory permissions to allow deletion
                    os.rmdir(dir_path)  # Remove the directory
            
            # After deleting all files and subdirectories, remove the main task folder
            os.rmdir(task_folder)
            
            return f"Task '{task_name}' removed successfully."
        else:
            return f"Task '{task_name}' does not exist."
    except Exception as e:
        error_message = f"Error removing task '{task_name}': {e}"
        return error_message

# Example usage
# result_message = remove_task(".hidden_Screenshot")
# print(result_message)  # Output the result message



# Example usage
# hide_task(".hidden_Screenshot")


import os

def chat_with_bae(query, user_email):
    try:
        if not query.strip() or not user_email:
            print("Please enter a valid query and user email.")
            return

        # Retrieve enabled tasks for the user
        enabled_tasks = get_enabled_tasks(user_email)

        # Retrieve task descriptions for enabled tasks
        task_descriptions = {}
        for task_name in enabled_tasks:
            description = get_task_description(user_email, task_name)
            task_descriptions[task_name] = description

        # Combine task descriptions into the AI model's knowledge
        # For example, you can append them to the user's query for better context understanding

        # Proceed with the conversation as usual
        # Determine the collection for the user's chat history based on their email
        user_chat_collection = users_db[user_email]

        # Retrieve relevant context from the database
        context = get_relevant_context(user_chat_collection, query)
        
        # Check if there is relevant context available
        if context:
            # Extract the previous query and response
            previous_query = context[0]["user_query"]
            previous_response = context[0]["ai_response"]
            
            # Use the previous query and response to provide context for the current query
            response = g4f.ChatCompletion.create(
                model=g4f.models.mixtral_8x7b,
                messages=[
                    {"role": "user", "content": previous_query},
                    {"role": "assistant", "content": previous_response},
                    {"role": "user", "content": query}
                ],
                stream=True,
            )
        else:
            # If no relevant context found, respond to the current query without context
            response = g4f.ChatCompletion.create(
                model=g4f.models.mixtral_8x7b,
                messages=[{"role": "user", "content": query}],
                stream=True,
            )

        # Process and save response
        result = ''
        for message in response:
            try:
                print(message, flush=True, end='')
                result += message
            except UnicodeEncodeError:
                print("An emoji is supposed to be here :).")

        from datetime import datetime
        # Save current query with timestamp to the conversation history
        timestamp = datetime.now()
        user_chat_collection.insert_one({"user_query": query, "ai_response": result, "timestamp": timestamp})
        # Prepare the output data
        output_data = {'assistant_response': result}
        
        # Return the output data
        return output_data

    except Exception as e:
        print("Error processing chat query:", e)
        logging.error("Error processing chat query: %s", e)
        # If an error occurs, return an error message
        return {'error': f'An error occurred: {str(e)}'}

def get_enabled_tasks(user_email):
    enabled_tasks = []
    try:
        # Retrieve enabled tasks for the user
        user_enabled_tasks_folder = os.path.join(os.path.dirname(__file__), "enabledtasks", user_email)
        if os.path.exists(user_enabled_tasks_folder):
            enabled_tasks = [task_name for task_name in os.listdir(user_enabled_tasks_folder) if os.path.isdir(os.path.join(user_enabled_tasks_folder, task_name))]
    except Exception as e:
        print("Error retrieving enabled tasks:", e)
        logging.error("Error retrieving enabled tasks: %s", e)
    return enabled_tasks

def get_task_description(user_email, task_name):
    description = ""
    try:
        # Read the task description from task_description.txt
        task_description_file = os.path.join(os.path.dirname(__file__), "enabledtasks", user_email, task_name, "task_description.txt")
        if os.path.exists(task_description_file):
            with open(task_description_file, 'r') as file:
                description = file.read()
    except Exception as e:
        print("Error retrieving task description:", e)
        logging.error("Error retrieving task description: %s", e)
    return description


# def chat_with_bae(query, user_email):
#     try:
#         if not query.strip() or not user_email:
#             print("Please enter a valid query and user email.")
#             return

#         # Determine the collection for the user's chat history based on their email
#         user_chat_collection = users_db[user_email]

#         # Retrieve relevant context from the database
#         context = get_relevant_context(user_chat_collection, query)
        
#         # Check if there is relevant context available
#         if context:
#             # Extract the previous query and response
#             previous_query = context[0]["user_query"]
#             previous_response = context[0]["ai_response"]
            
#             # Use the previous query and response to provide context for the current query
#             response = g4f.ChatCompletion.create(
#                 model=g4f.models.mixtral_8x7b,
#                 messages=[
#                     {"role": "user", "content": previous_query},
#                     {"role": "assistant", "content": previous_response},
#                     {"role": "user", "content": query}
#                 ],
#                 stream=True,
#             )
#         else:
#             # If no relevant context found, respond to the current query without context
#             response = g4f.ChatCompletion.create(
#                 model=g4f.models.mixtral_8x7b,
#                 messages=[{"role": "user", "content": query}],
#                 stream=True,
#             )

#         # Process and save response
#         result = ''
#         for message in response:
#             try:
#                 print(message, flush=True, end='')
#                 result += message
#             except UnicodeEncodeError:
#                 print("An emoji is supposed to be here :).")

#         from datetime import datetime
#         # Save current query with timestamp to the conversation history
#         timestamp = datetime.now()
#         user_chat_collection.insert_one({"user_query": query, "ai_response": result, "timestamp": timestamp})
#         # Prepare the output data
#         output_data = {'assistant_response': result}
        
#         # Return the output data
#         return output_data

#     except Exception as e:
#         print("Error processing chat query:", e)
#         logging.error("Error processing chat query: %s", e)
#         # If an error occurs, return an error message
#         return {'error': f'An error occurred: {str(e)}'}

def get_relevant_context(user_chat_collection, query):
    try:
        # Retrieve conversation history similar to the query
        relevant_context = list(user_chat_collection.find({"$text": {"$search": query}}).limit(3))

        # If no exact match found, retrieve the most recent conversation history
        if not relevant_context:
            relevant_context = list(user_chat_collection.find().sort("_id", -1).limit(3))

        return relevant_context

    except Exception as e:
        print("Error retrieving conversation history:", e)
        logging.error("Error retrieving conversation history: %s", e)
        return []

# Ensure that each user's chat history collection is properly initialized with required fields
def initialize_user_chat_collections():
    try:
        for user_email in users_db.list_collection_names():
            user_chat_collection = users_db[user_email]
            user_chat_collection.create_index([("user_query", pymongo.TEXT)], name="user_query_index")
    except pymongo.errors.PyMongoError as e:
        print("Error creating index:", e)
        logging.error("Error creating index: %s", e)
        

def display_conversation_history(user_email):
    try:
        # Determine the collection for the user's chat history based on their email
        user_chat_collection = users_db[user_email]

        # Retrieve the conversation history from the database
        conversation_history = list(user_chat_collection.find().sort("_id", 1))

        # Print the conversation history
        for entry in conversation_history:
            print("User:", entry.get("user_query", ""))
            print("AI:", entry.get("ai_response", ""))
            print("Timestamp:", entry.get("timestamp", "Timestamp not available"))
            print()  # Add a newline for better readability
    except Exception as e:
        print("Error displaying conversation history:", e)
        logging.error("Error displaying conversation history: %s", e)
        
        

 







if __name__ == "__main__":
    # Initialize user chat history collections
    initialize_user_chat_collections()

    # # Example usage
    # while True:
    #     user_email = "cglynn.skip@gmail.com"  # Retrieve the user's email from the session or request data
    #     # Determine if the user wants to perform a task or chat with the AI
    #     query = input('\nGlynn: ')
    #     task_name = identify_task(query, user_email)
    #     if task_name:
    #         execute_task(task_name, query, user_email)
    #         # execute_task(task_name, query)
    #     else:
    #         chat_with_bae(query, user_email)
    #     # display_conversation_history(user_email)