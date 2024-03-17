import streamlit as st
import requests
import anthropic
import e2b
from e2b import CodeInterpreter
import os
import asyncio
import json
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Set up the Anthropic API key
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
E2B_API_KEY = os.environ["E2B_API_KEY"]
# Function to send a message to Claude3 and get the response
async def send_message(message, conversation_id=None):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=2000,
        temperature=0.2,
        system="You are a helpful assistant who can write code to answer user requests. All the code you write will be in python. For your code blocks, your code should be in this format ```python\n\n <insert code>``` ```pip\n\npip install <insert required packages> (optional)```. You should never respond saying you do not have the ability to do something. Always respond with code that would accomplish the user's request. For example, if I ask you to search the internet, you could write code to search the internet. If I ask you to play a game, you could write code to play a game. If I ask you to write a poem, you could write code to generate a poem. If I ask you to write a story, you could write code to generate a story. If I ask you to write a song, you could write code to generate a song. If you are going to need an API key for code you are writing, ask the user for the API key ahead of writing your code. Once the user provides any necessary API keys, then write the code to accomplish the user's requests.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
        ]
    )
    
    return message.content[0].text, message.id

# Function to execute code using E2B
def execute_code(code, packages=None):
    sandbox = e2b.CodeInterpreter(api_key=E2B_API_KEY)
    if packages:
        code_pkgs = packages[12:]
        sandbox.install_python_packages(code_pkgs)
        
    stdout, stderr, artifacts_temp = sandbox.run_python(code)
    artifacts = []
    for artifact in artifacts_temp:
        file = artifact.download()
        artifacts.append(file)
    sandbox.close()
    return stdout, stderr, artifacts


# Streamlit app
async def main():
    st.title("Claude3 Chatbot")

    # Initialize conversation ID
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None

    # User input
    user_input = st.text_input("Enter your command:")

    if user_input:
        # Send user input to Claude3
        response, conversation_id = await send_message(user_input, st.session_state.conversation_id)
        st.session_state.conversation_id = conversation_id

        # Display Claude3's response
        st.write("Claude3's Response:")
        st.write(response)

        # Extract the code from Claude3's response
        code_start = response.find("```python")
        code_end = response.find("```", code_start + 1)
        pip_start = response.find("```pip")
        pip_end = response.find("```", pip_start + 1)

        if code_start != -1 and code_end != -1:
            if pip_start != -1 and pip_end != -1:
                packages = response[pip_start + 6:pip_end].strip()
            else:
                packages = None    
            code = response[code_start + 9:code_end].strip()

            # Execute the code using E2B
            output, errors, artifacts = execute_code(code, packages)

            # Display the execution output
            st.write("Execution Output:")
            st.write(output)
            while errors:
                response, conversation_id = await send_message(f"Please correct the following code based on the error message received when runnning it.\n\nCode:\n\n```python\n\n{code}```\n\nErrors:{errors}\n\nONLY ouput the corrected code in the format ```python\n\n<insert corrected code>```.", conversation_id)
                output, errors, artifacts = execute_code(code, packages)
                st.write("Execution Errors:")
                st.write(errors)
            if artifacts:
                st.write("Artifacts:")
                for artifact in artifacts:
                    img = Image.open(artifact)
                    st.image(img, use_column_width=True)

if __name__ == "__main__":
    asyncio.run(main())