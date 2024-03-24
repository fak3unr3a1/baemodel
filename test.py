



# import os
# import spacy
# import pymongo
# import g4f
# from difflib import SequenceMatcher
# import logging

# # Configure logging
# logging.basicConfig(filename='bae.log', level=logging.ERROR)

# # Load the English language model for spaCy
# nlp = spacy.load("en_core_web_sm")

# # Connect to MongoDB Atlas
# try:
#     client = pymongo.MongoClient("mongodb+srv://UNR3A1:JXoO1X4EY6iArT0E@baemodelcluster.yvin3kv.mongodb.net/")
#     db = client["chat_history"]  # Connecting to the "chat_history" database
#     users_db = client["user_database"]  # Connecting to the "user_database" database
# except pymongo.errors.ConnectionFailure as e:
#     print("Failed to connect to MongoDB Atlas:", e)
#     logging.error("Failed to connect to MongoDB Atlas: %s", e)
    
    
    
# def similar(a, b):
#     return SequenceMatcher(None, a, b).ratio()

# def execute_task(task_name):
#     try:
#         project_folder = r"C:\Users\cglyn\BAE4\B.A.E\usertasks"
#         filename = os.path.join(project_folder, task_name, f"task.py")  # Adjusted file path
#         with open(filename, "r") as file:
#             code = file.read()
#         exec(code)
#     except FileNotFoundError as e:
#         print("Task file not found:", e)
#         logging.error("Task file not found: %s", e)
#     except Exception as e:
#         print("Error executing task:", e)
#         logging.error("Error executing task: %s", e)

# def identify_task(query):
#     try:
#         project_folder = r"C:\Users\cglyn\BAE4\B.A.E\usertasks"
#         query_keywords = set(token.text for token in nlp(query) if not token.is_stop)
#         best_match_folder = None
#         best_match_score = 0.0

#         for folder_name in os.listdir(project_folder):
#             folder_path = os.path.join(project_folder, folder_name)
#             if os.path.isdir(folder_path):
#                 description_file = os.path.join(folder_path, 'task_description.txt')
#                 if os.path.exists(description_file):
#                     # Read the task description from the file
#                     with open(description_file, 'r') as desc_file:
#                         description = desc_file.read()
                    
#                     # Preprocess the task description
#                     desc_doc = nlp(description)
#                     desc_keywords = set(token.text for token in desc_doc if not token.is_stop)
                    
#                     # Calculate similarity between query and task description
#                     score = len(query_keywords.intersection(desc_keywords)) / len(query_keywords.union(desc_keywords))
                    
#                     # Update best match folder
#                     if score > best_match_score:
#                         best_match_folder = folder_name
#                         best_match_score = score

#         return best_match_folder
#     except Exception as e:
#         print("Error identifying task:", e)
#         logging.error("Error identifying task: %s", e)

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

#         # Save current query to the conversation history
#         user_chat_collection.insert_one({"user_query": query, "ai_response": result})

#         # Prepare the output data
#         output_data = {'assistant_response': result}
        
#         # Return the output data
#         return output_data

#     except Exception as e:
#         print("Error processing chat query:", e)
#         logging.error("Error processing chat query: %s", e)
#         # If an error occurs, return an error message
#         return {'error': f'An error occurred: {str(e)}'}

# def get_relevant_context(user_chat_collection, query):
#     try:
#         # Retrieve conversation history similar to the query
#         relevant_context = list(user_chat_collection.find({"$text": {"$search": query}}).limit(3))

#         # If no exact match found, retrieve the most recent conversation history
#         if not relevant_context:
#             relevant_context = list(user_chat_collection.find().sort("_id", -1).limit(3))

#         return relevant_context

#     except Exception as e:
#         print("Error retrieving conversation history:", e)
#         logging.error("Error retrieving conversation history: %s", e)
#         return []

# # Ensure that each user's chat history collection is properly initialized with required fields
# def initialize_user_chat_collections():
#     try:
#         for user_email in users_db.list_collection_names():
#             user_chat_collection = users_db[user_email]
#             user_chat_collection.create_index([("user_query", pymongo.TEXT)], name="user_query_index")
#     except pymongo.errors.PyMongoError as e:
#         print("Error creating index:", e)
#         logging.error("Error creating index: %s", e)

# if __name__ == "__main__":
#     # Initialize user chat history collections
#     initialize_user_chat_collections()

#     # Example usage
#     while True:
#         user_email = "cglynn.skip@gmail.com"  # Retrieve the user's email from the session or request data
#         query = input("User: ")  # User's query
#         chat_with_bae(query, user_email)

# from flask import Flask, request, session, jsonify
# import pymongo

# app = Flask(__name__)
# app.secret_key = 'your_secret_key_here'  # Set a secret key for session management

# # Connect to MongoDB Atlas
# client = pymongo.MongoClient("mongodb+srv://UNR3A1:JXoO1X4EY6iArT0E@baemodelcluster.yvin3kv.mongodb.net/")
# db = client["chat_history"]  # Connecting to the "chat_history" database
# users_db = client["user_database"]  # Connecting to the "user_database" database

# @app.route('/chat', methods=['POST'])
# def chat_with_bae():
#     try:
#         user_email = session.get('user_email')  # Retrieve the user's email from the session
        
#         if not user_email:
#             return jsonify({'error': 'User email not found in session'}), 400

#         query = request.json.get('query')  # Assuming the user's query is sent in the request body
        
#         if not query:
#             return jsonify({'error': 'No query provided'}), 400

#         # Determine the collection for the user's chat history based on their email
#         user_chat_collection = users_db[user_email]

#         # Retrieve relevant context from the database
#         context = get_relevant_context(user_chat_collection, query)
        
#         # Chat processing logic...
        
#         return jsonify({'response': 'Your response here'})

#     except Exception as e:
#         return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# def get_relevant_context(user_chat_collection, query):
#     # Retrieve conversation history similar to the query
#     relevant_context = list(user_chat_collection.find({"$text": {"$search": query}}).limit(3))

#     # If no exact match found, retrieve the most recent conversation history
#     if not relevant_context:
#         relevant_context = list(user_chat_collection.find().sort("_id", -1).limit(3))

#     return relevant_context

# if __name__ == '__main__':
#     app.run(debug=True)
