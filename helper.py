# Add your utilities or helper functions to this file.

import os
from dotenv import load_dotenv, find_dotenv
from IPython.display import display, HTML
import json
import html
import re
from typing import Optional

# these expect to find a .env file at the directory above the lesson.                                                                                                                     # the format for that file is (without the comment)                                                                                                                                       #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService                                                                                                                                     
def load_env():
    _ = load_dotenv(find_dotenv())

def get_openai_api_key():
    load_env()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return openai_api_key



def nb_print(messages):
    html_output = """
    <style>
        .message-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            background-color: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
            color: #d4d4d4;
        }
        .message {
            padding: 10px 15px;
            border-bottom: 1px solid #3a3a3a;
        }
        .message:last-child {
            border-bottom: none;
        }
        .title {
            font-weight: bold;
            margin-bottom: 5px;
            color: #ffffff;
            text-transform: uppercase;
            font-size: 0.9em;
        }
        .content {
            background-color: #2d2d2d;
            border-radius: 4px;
            padding: 5px 10px;
            font-family: 'Consolas', 'Courier New', monospace;
            white-space: pre-wrap;
        }
        .status-line {
            margin-bottom: 5px;
            color: #d4d4d4;
        }
        .function-name { color: #569cd6; }
        .json-key { color: #9cdcfe; }
        .json-string { color: #ce9178; }
        .json-number { color: #b5cea8; }
        .json-boolean { color: #569cd6; }
        .internal-monologue { font-style: italic; }
    </style>
    <div class="message-container">
    """

    for msg in messages:
        content = get_formatted_content(msg)

        # don't print empty function returns
        if msg.message_type == "function_return":
            return_data = json.loads(msg.function_return)
            if "message" in return_data and return_data["message"] == "None":
                continue

        title = msg.message_type.replace('_', ' ').upper()
        html_output += f"""
        <div class="message">
            <div class="title">{title}</div>
            {content}
        </div>
        """

    html_output += "</div>"
    display(HTML(html_output))

def get_formatted_content(msg):
    if msg.message_type == "internal_monologue":
        return f'<div class="content"><span class="internal-monologue">{html.escape(msg.internal_monologue)}</span></div>'
    elif msg.message_type == "function_call":
        args = format_json(msg.function_call.arguments)
        return f'<div class="content"><span class="function-name">{html.escape(msg.function_call.name)}</span>({args})</div>'
    elif msg.message_type == "function_return":

        return_value = format_json(msg.function_return)
        #return f'<div class="status-line">Status: {html.escape(msg.status)}</div><div class="content">{return_value}</div>'
        return f'<div class="content">{return_value}</div>'
    elif msg.message_type == "user_message":
        if is_json(msg.message):
            return f'<div class="content">{format_json(msg.message)}</div>'
        else:
            return f'<div class="content">{html.escape(msg.message)}</div>'
    elif msg.message_type in ["assistant_message", "system_message"]:
        return f'<div class="content">{html.escape(msg.message)}</div>'
    else:
        return f'<div class="content">{html.escape(str(msg))}</div>'

def is_json(string):
    try:
        json.loads(string)
        return True
    except ValueError:
        return False

def format_json(json_str):
    try:
        parsed = json.loads(json_str)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        formatted = formatted.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        formatted = formatted.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
        formatted = re.sub(r'(".*?"):', r'<span class="json-key">\1</span>:', formatted)
        formatted = re.sub(r': (".*?")', r': <span class="json-string">\1</span>', formatted)
        formatted = re.sub(r': (\d+)', r': <span class="json-number">\1</span>', formatted)
        formatted = re.sub(r': (true|false)', r': <span class="json-boolean">\1</span>', formatted)
        return formatted
    except json.JSONDecodeError:
        return html.escape(json_str)

def read_resume(self, name: str): 
    """
    Read the resume data for a candidate given the name

    Args: 
        name (str): Candidate name 

    Returns: 
        resume_data (str): Candidate's resume data 
    """
    import os
    filepath = os.path.join("data", "resumes", name.lower().replace(" ", "_") + ".txt")
    #print("read", filepath)
    return open(filepath).read()

def submit_evaluation(
    self, 
    candidate_name: str, 
    reach_out: bool, 
    resume: str, 
    justification: str
): 
    """
    Submit a candidate for outreach. 

    Args: 
        candidate_name (str): The name of the candidate
        reach_out (bool): Whether to reach out to the candidate
        resume (str): The text representation of the candidate's resume 
        justification (str): Justification for reaching out or not
    """
    from letta import create_client 
    client = create_client()

    message = "Reach out to the following candidate. " \
    + f"Name: {candidate_name}\n" \
    + f"Resume Data: {resume}\n" \
    + f"Justification: {justification}"
    print("eval agent", candidate_name)
    if reach_out:
        response = client.send_message(
            agent_name="outreach_agent", 
            role="user", 
            message=message
        ) 
    else: 
        print(f"Candidate {candidate_name} is rejected: {justification}")

def email_candidate(self, content: str): 
    """
    Send an email

    Args: 
        content (str): Content of the email 
    """
    print("Pretend to email:", content)
    return

def search_candidates_db(self, page: int) -> Optional[str]: 
    """
    Returns 1 candidates per page. 
    Must start at page 0.
    Page 0 returns the first 1 candidate, 
    Page 1 returns the next 1, etc.
    Returns `None` if no candidates remain. 

    Args: 
        page (int): The page number to return candidates from 

    Returns: 
        candidate_names (List[str]): Names of the candidates
    """
    
    names = ["Tony Stark", "Spongebob Squarepants", "Gautam Fang"]
    if page >= len(names): 
        return None
    return names[page]

def consider_candidate(self, name: str): 
    """
    Submit a candidate for consideration. 

    Args: 
        name (str): Candidate name to consider 
    """
    from letta import create_client 
    client = create_client()
    message = f"Consider candidate {name}" 
    print("Sending message to eval agent: ", message)
    response = client.send_message(
        agent_name="eval_agent", 
        role="user", 
        message=message
    ) 
    nb_print(response.messages)