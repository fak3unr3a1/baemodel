import os
from datetime import datetime
from openai import OpenAI
from bae import get_enabled_tasks, get_task_description, get_relevant_context, initialize_user_chat_collections, identify_task, is_task_enabled, execute_task
import logging
import pymongo

# Initialize OpenAI client
openai_client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Connect to MongoDB Atlas
try:
    mongo_client = pymongo.MongoClient("mongodb+srv://UNR3A1:JXoO1X4EY6iArT0E@baemodelcluster.yvin3kv.mongodb.net/")
    db = mongo_client["chat_history"]  # Connecting to the "chat_history" database
    users_db = mongo_client["user_database"]  # Connecting to the "user_database" database
except pymongo.errors.ConnectionFailure as e:
    print("Failed to connect to MongoDB Atlas:", e)
    logging.error("Failed to connect to MongoDB Atlas: %s", e)


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
            chat_completion = openai_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": previous_query},
                    {"role": "assistant", "content": previous_response},
                    {"role": "user", "content": query}
                ],
                model="gpt-3.5-turbo",
            )
        else:
                   chat_completion = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": query}],
            model="gpt-3.5-turbo",
        )

        result = ''  # Define result variable here
        try:
            # Your code to process and save response
            for message in chat_completion.choices[0].message.content:
                try:
                    print(message, flush=True, end='')
                    result += message
                except UnicodeEncodeError:
                    print("An emoji is supposed to be here :).")
        except Exception as e:
            print("Error processing chat query:", e)
            logging.error("Error processing chat query: %s", e)
            result = f'An error occurred: {str(e)}'  # Assign a default value in case of an error

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


if __name__ == "__main__":
    # Initialize user chat history collections
    initialize_user_chat_collections()

    # Example usage
    while True:
        user_email = "glynn.kiprotich@gmail.com"  # Retrieve the user's email from the session or request data
        # Determine if the user wants to perform a task or chat with the AI
        query = input('\nGlynn: ')
        user_chat_collection = users_db[user_email]

        task_name = identify_task(query, user_email)
        if task_name:
            execute_task(task_name, query, user_email)
            # execute_task(task_name, query)
        else:
            chat_with_bae(query, user_email)
        # display_conversation_history(user_email)
