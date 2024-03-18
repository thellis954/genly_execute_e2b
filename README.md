# PROOF OF CONCEPT - EXECUTING CODE USING E2B

## Description

This is a POC project showing how an Anthropic chat bot can write code, then use E2B to execute the code.  

NEEDED FOR FULL FUNCTIONALITY: Would need to actually provide the "recipes" and "API documentation" as well as API keys or auth tokens to Anthropic to get code that is executable back to E2B.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/thellis954/genly_execute_e2b
    ```

2. Navigate to the project directory:

    ```bash
    cd genly_execute_e2b
    ```

3. Install the requirements:

    ```bash
    python3 -m venv .venv --prompt="genly_execute_e2b"
    source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run main.py
    ```

## DEBUGGING Usage

1. Open the project in VSCode.

2. Go to the Debug panel.

3. Select "Debug Streamlit" from the debugger configuration window.

4. Click the "Start Debugging" button or press F5 to run the app.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).