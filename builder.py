#builder.py

import re
import g4f
import ast
import sys
from io import StringIO

def generate_chat_response(model, messages, context=10):
    response = g4f.ChatCompletion.create(
        model=model,
        messages=messages,
        stream=True,
        context=context,
    )

    result = ''
    for message in response:
        try:
            print(message, flush=True, end='')
            result += message
        except UnicodeEncodeError:
            print("An emoji is supposed to be here :).")
    
    return result

def execute_code(code):
    # Redirect stdout to capture the output of the executed code
    old_stdout = sys.stdout
    new_stdout = StringIO()
    sys.stdout = new_stdout

    try:
        # Execute the provided code
        exec(code)
        output = new_stdout.getvalue().strip()
        return output
    finally:
        # Restore the original stdout
        sys.stdout = old_stdout

def understand_query_and_generate_list(query):
    messages = [
        {"role": "user", "content": query},
        {"role": "system", "content": "List down the expected returns for the user query."},
        {"role": "system", "content": "After giving what is expected, clearly breakdown how the required query can be performed up until the very end."},
    ]
    model = g4f.models.mixtral_8x7b
    return generate_chat_response(model, messages)

def perform_actions_and_get_results(expected_results):
    # Placeholder code for demonstration
    actions_results = expected_results
    
    messages = [
        {"role": "user", "content": expected_results},
        {"role": "system", "content": actions_results},
    ]
    model = g4f.models.mixtral_8x7b  # You can use a different model for this step if needed
    return generate_chat_response(model, messages)

def evaluate_results(user_query, generated_results):
    while True:
        # Convert both user_query and generated_results to lowercase for case-insensitive comparison
        user_query = user_query.lower()
        generated_results = generated_results.lower()

        # Check if the generated_results contain the user_query
        if user_query in generated_results:
            evaluation_result = "Evaluation: Results match what the user required.\n"
            break
        else:
            print("Results do not match what the user required. Redoing the process...\n")
            # Call the function to redo the process and generate new results
            generated_results = perform_actions_and_get_results(understand_query_and_generate_list(user_query))
            # Update user_query with the original query since it might have been modified during the loop
            user_query = user_query.lower()

    return evaluation_result

## Example usage:
# user_query = "write code to send money to someone on mpesa. I will need a field where i will input their phone number and another to input the amount"
# expected_results = understand_query_and_generate_list(user_query)
# actions_results = perform_actions_and_get_results(expected_results)

# #Extract code snippet using regular expressions
# code_snippet_match = re.search(r'```python\n(.+?)```', actions_results, re.DOTALL)
# if code_snippet_match:
    # code_snippet = code_snippet_match.group(1)
# else:
    # print("Error: No code snippet found in the response.")
    # sys.exit(1)

# # Parse the code snippet to execute it
# try:
#     parsed_code = ast.parse(code_snippet, mode='exec')
#     executed_output = execute_code(code_snippet)
#     evaluation = evaluate_results(user_query, executed_output)
#     print("Evaluation:", evaluation)
# except Exception as e:
#     print("Error executing the code snippet:", e)


