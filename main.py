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
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS"))
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE"))
E2B_API_KEY = os.environ["E2B_API_KEY"]

# Function to send a message to Claude3 and get the response
async def send_message(message, conversation_id=None, context=None):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    prompt=f"""You are a helpful assistant who can write python code that return values that help to answer user requests. All the code you write will be in python. For your code blocks, your code should be in this format ```python\n\n <insert code>``` ```pip\n\npip install <insert required packages> (optional)```. You should never respond saying you do not have the ability to do something. Always respond with code that would accomplish the user's request. For example, if I ask you to search the internet, you could write code to search the internet. If I ask you to play a game, you could write code to play a game. If I ask you to write a poem, you could write code to generate a poem. If I ask you to write a story, you could write code to generate a story. If I ask you to write a song, you could write code to generate a song. If you write code that uses an API or SDK, if authentication is required for the API or SDK, ensure you include code to authenticate the user using OAuth in a browser, or via API key if you are provided one in the Additional Context. At the end of the code, the python code should print a summary of what it did and summary of the outputs of the actions taken.
                    
                    Response FORMAT example:\n\n
                    ###OPTIONAL IF YOU NEED TO INSTALL PACKAGES - include all libraries on one line after 'pip install'
                    ```pip\n\n 
                    pip install requests python-dotenv
                    ```
                    ###END OPTIONAL
                    ```python\n\n
                    <insert code>
                    print("<insert summary of what the code did and any outputs>")
                    ```
                    Human Request: {message}\n\n
                    Additional Context: {context}\n\n
                    Answer: 
                    ###OPTIONAL IF YOU NEED TO INSTALL PACKAGES
                    ```pip\n\n
                    pip install <insert required packages> 
                    ```
                    ###END OPTIONAL
                    ```python\n\n
                        
                           
                    ```
        """
    msg = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MODEL_MAX_TOKENS,
        temperature=MODEL_TEMPERATURE,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    
    return msg.content[0].text, msg.id

# Function to send a message to Claude3 and get the response
async def correct_code(message, conversation_id=None):
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MODEL_MAX_TOKENS,
        temperature=MODEL_TEMPERATURE,
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


def execute_code(code, packages=None):
    EXECUTE_LOCALLY = os.getenv("EXECUTE_LOCALLY")
    if EXECUTE_LOCALLY == "True":
        if packages:
            code_pkgs = packages[12:]
            os.system(f"pip install {code_pkgs} > temp_install_log.txt 2>&1")
            os.system(f"pip3 freeze > requirements.txt")
        with open("temp.py", "w") as file:
            file.write(code)
        os.system(f"python temp.py > temp.txt 2>&1")
        with open("temp.txt", "r") as file:
            output = file.read()

        return output, "", []
    else:
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
async def get_llm_analysis(code_output, human_question):
    prompt= f"""
            Take the Code Output below as context, and the original human question, and write a user friendly, html-markup formatted response to the human question - including links, sources and/or images if relevant.\n\n
            Code Output: {code_output}\n\n
            Human Request: {human_question}\n\n
            Answer:\n\n
        """
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MODEL_MAX_TOKENS,
        temperature=0.8,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    msg = message.content[0].text
    return msg

def parse_response(response):
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
    return code, packages

def cleanup():
    if os.path.exists("temp.py"):
        os.remove("temp.py")
    if os.path.exists("temp.txt"):
        os.remove("temp.txt")
    if os.path.exists("temp_install_log.txt"):
        os.remove("temp_install_log.txt")
    if os.path.exists("token.json"):
        os.remove("token.json")

# Streamlit app
async def main():
    st.title("Genly AI Executor")

    # Initialize conversation ID
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "context" not in st.session_state:
        st.session_state.context = os.getenv("ADDITIONAL_CONTEXT")

    # User input
    user_input = st.text_input("Enter your command:")

    if user_input:
        # Send user input to Claude3
        with st.spinner("Thinking..."):
            response, conversation_id = await send_message(user_input, st.session_state.conversation_id, st.session_state.context)
            st.session_state.conversation_id = conversation_id
            code, packages = parse_response(response)

        with st.expander("Claude3's Response and Code", expanded=False):
            # Display Claude3's response
            st.write("Claude3's Response:")
            st.write(response)

            with st.spinner("Running the code"):
                # Execute the code using E2B
                output, errors, artifacts = execute_code(code, packages)
                if errors.find("completed") != -1:
                    errors = ""

            
        while errors or output.find("Failed to retrieve") != -1 or output.find("Status code:") != -1 or output.find("Traceback") != -1:
            st.write("Execution Errors:")
            st.write(output + "\n" + errors)
            with st.spinner("Correcting my code"):
                prompt = f"""Please review the following code and the resulting error. Then, fix the code or come up with a new approach to accomplish the original human request, and write new code to accomplish the request. ONLY respond with python code and nothing else.\n\n
                Code:\n\n
                ```python\n\n{code}```\n\n
                
                Errors:{output + errors}\n\n
            
                
                Response FORMAT example:\n\n
                ###OPTIONAL IF YOU NEED TO INSTALL PACKAGES - include all libraries on one line after 'pip install'
                ```pip\n\n 
                pip install requests
                ```
                ###END OPTIONAL
                ```python\n\n
                <insert code>
                ```
                Human Request: {user_input}\n\n
                Additional Context: {st.session_state.context}\n\n
                Answer: 
                ###OPTIONAL IF YOU NEED TO INSTALL PACKAGES
                ```pip\n\n
                pip install <insert required packages> 
                ```
                ###END OPTIONAL
                ```python\n\n
                ```
            """
            response, conversation_id = await correct_code(prompt, conversation_id)
            with st.expander("Corrected Code", expanded=False):
                st.write(response)
            with st.spinner("Running the corrected code"):
                code, packages = parse_response(response)
                output, errors, artifacts = execute_code(code, packages)
        # Display the execution output
        with st.expander("Execution Output", expanded=False):
            st.write("Execution Output:")
            st.markdown(output, unsafe_allow_html=True)
        
        msg = await get_llm_analysis(output, user_input)
        st.markdown(msg, unsafe_allow_html=True)
        if artifacts:
            st.write("Artifacts:")
            for artifact in artifacts:
                img = Image.open(io.BytesIO(artifact))
                width = img.width
                height = img.height
                st.image(img, use_column_width=True)
        cleanup()            
if __name__ == "__main__":
    asyncio.run(main())