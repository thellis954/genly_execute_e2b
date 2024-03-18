import streamlit as st
import requests
import anthropic
import e2b
from e2b import CodeInterpreter
import os
import asyncio
import json
import io
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

# Function to send a message to Claude3 and get the response
async def correct_code(message, conversation_id=None):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=2000,
        temperature=0.2,
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
        with st.spinner("Thinking..."):
            response, conversation_id = await send_message(user_input, st.session_state.conversation_id)
            st.session_state.conversation_id = conversation_id

        with st.expander("Claude3's Response and Code", expanded=False):
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

            with st.spinner("Running the code"):
                # Execute the code using E2B
                output, errors, artifacts = execute_code(code, packages)
                if errors.find("completed") != -1:
                    errors = ""

            
            while errors or output.find("Failed to retrieve") != -1 or output.find("Status code:") != -1:
                st.write("Execution Errors:")
                st.write(output + "\n" + errors)
                with st.spinner("Correcting my code"):
                    prompt = f"""Please review the following code and the resulting error. Then, fix the code or come up with a new approach to accomplish the original human request, and write new code to accomplish the request. ONLY respond with python code and nothing else.\n\n
                    Code:\n\n
                    ```python\n\n{code}```\n\n
                    
                    Errors:{output + errors}\n\n
                    
                    Human Request: {user_input}\n\n
                    
                    Response example:\n\n
                    ###OPTIONAL IF YOU NEED TO INSTALL PACKAGES
                    ```pip\n\n 
                    pip install requests
                    ```
                    ###END OPTIONAL
                    ```python\n\n
                        def my_function():
                            # Your code here
                    ```

                    Answer: 
                    
                """
                response, conversation_id = await correct_code(prompt, conversation_id)
                with st.expander("Corrected Code", expanded=False):
                    st.write(response)
                with st.spinner("Running the corrected code"):
                    # Extract the code from Claude3's response
                    code_start = response.find("```python")
                    code_end = response.find("```", code_start + 1)
                    pip_start = response.find("```pip")
                    pip_end = response.find("```", pip_start + 1)
                    if pip_start != -1 and pip_end != -1:
                        packages = response[pip_start + 6:pip_end].strip()
                    else:
                        packages = None    
                    code = response[code_start + 9:code_end].strip()
                    output, errors, artifacts = execute_code(code, packages)
            # Display the execution output
            
            st.write("Execution Output:")
            st.markdown(output, unsafe_allow_html=True)

            if artifacts:
                st.write("Artifacts:")
                for artifact in artifacts:
                    img = Image.open(io.BytesIO(artifact))
                    width = img.width
                    height = img.height
                    st.image(img, use_column_width=True)

if __name__ == "__main__":
    asyncio.run(main())