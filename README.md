# Multi AI Agent Collaboration System

## Introduction

This repository demonstrates a **multi-agent collaboration system** designed using the powerful [Letta](https://letta.com/) framework [GitHub](https://github.com/letta-ai/letta). The system employs three agents that collaborate via individual and shared memory blocks, leveraging state-of-the-art LLMs for intelligent decision-making and communication. 
This project is designed for the automated review of candidate resumes to assess their qualifications for a company's job requirements. It also handles generating acceptance or rejection emails to candidates for interview scheduling.

## Table of Contents
- [Agents Overview](#agents-overview)
- [Agents Collaboration Details](#agents-collaboration-details)
- [Key Features](#key-features)
- [Installation](#installation)
- [Usage](#usage)
- [Memory Management](#memory-management)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
---

### Agents Overview

1. **Recruiter Agent**:
   - Role: Acts as the orchestrator, gathering candidate data and coordinating tasks between other agents.
   
2. **Evaluator Agent**:
   - Role: Evaluates candidate resumes and determines their suitability.
   
3. **Outreach Agent**:
   - Role: Drafts and sends personalized emails to candidates.

---
### Agents Collaboration Details

Each agent maintains its **own memory** while sharing a **common memory block** (`company block`). This enables effective collaboration by:
- Sending messages to each other.
- Leveraging shared knowledge from the `company block`.

---
### Key Features
- Powered by `gemma2 9b` locally using [ollama](https://ollama.ai/).
- Flexibility to integrate other models like **llama**, **OpenAI** (e.g., GPT-4).
- Showcases advanced memory management capabilities using `Letta`.

Letta framework designed with Agent as a Service principles, enabling seamless integration with external applications via REST APIs.

---

## Installation

Follow these steps to set up the project:

1. Clone the repository:
   ```bash
   git clone https://github.com/alirezafarzipour/multi-agent-collaboration.git
   cd multi-agent-collaboration
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the `ollama` model server locally:
   - Install [ollama](https://ollama.ai/).
   - Start the server using:
     ```bash
     ollama serve
     ```

4. Configure your LLM settings in the Python script:
   ```python
   from letta import create_client
   from letta.schemas.llm_config import LLMConfig

   client = create_client()

   llm_config = LLMConfig(
       model="gemma2:latest",
       provider="ollama",
       model_endpoint="http://localhost:11434",
       model_endpoint_type="ollama",
       context_window=8192,
       # params={"temperature": 0.7, "max_tokens": 512},
   )

   client.set_default_llm_config(llm_config)
   ```
To switch models, modify the `model` parameter in the configuration:

- Using `llama` models:
  ```python
  model="llama3.2"
  ```

- Using OpenAI models:
  Ensure you have set up your API key, then configure the client as follows:
  ```python
  from letta import create_client
  from letta.schemas.llm_config import LLMConfig
  
  client = create_client()
  client.set_default_llm_config(LLMConfig.default_config("gpt-4o-mini"))
  ```
---

## Usage

The code is provided as a Jupyter Notebook (`.ipynb`). You can run notebooks locally using **Jupyter Notebook** or in the cloud using **Google Colab**:

1. **Jupyter Notebook**:
   - Install Jupyter Notebook if not already installed:
     ```bash
     pip install notebook
     ```
   - Navigate to the directory of the desired module and run:
     ```bash
     jupyter notebook
     ```
   - Open the corresponding notebook file (e.g., `semantic_search.ipynb`) and execute the cells step by step.

2. **Google Colab**:
   - Upload the notebook to Google Colab:
     - Go to [Google Colab](https://colab.research.google.com/).
     - Click on `File > Upload Notebook` and upload the desired `.ipynb` file.
   - Install required dependencies in the first cell and proceed with the execution.

This structure allows for a user-friendly experience while experimenting with the modules.

---

## Memory Management

The `Letta` framework provides robust memory management features. Each agent can maintain its memory and access/update shared memory blocks.


Initial memory configuration for the `company block`:
```python
from letta.schemas.block import Block 

org_description= "The company is called AgentOS " \
+ "and is building AI tools to make it easier to create " \
+ "and deploy LLM agents."

org_block = Block(name="company", value=org_description )
```
---
## Examples

### Sending Personalized Emails

The `Outreach Agent` generates an email based on the company name in the shared memory block:
```python
response = client.send_message(
    agent_name="eval_agent", 
    role="user", 
    message="Candidate: Tony Stark"
)
```
```
eval agent Tony Stark
Pretend to email: Hi Tony,

We at AgentOS are building cutting-edge AI tools to make it easier to create and deploy LLM agents. We were very impressed with your background in React development and your academic achievements. Your experience in [mention specific relevant experience from resume] aligns perfectly with our needs.

We'd love to chat with you about how your skills could contribute to our mission. Are you available for a quick call next week?

Best,
Bob
AgentOS
```

### Updating Company Name in Memory

We can replace or correct data in memories by sending feedback to its agents. Example of replacing the company name from `AgentOS` to `FoundationAI`:
```python
feedback = "The company is also renamed to FoundationAI"
response = client.send_message(
    agent_name="eval_agent", 
    role="user", 
    message=feedback
)
```
After that, **eval_agent** uses the new information to evaluate candidates and writing emails:
```python
response = client.send_message(
    agent_name="eval_agent", 
    role="system", 
    message="Candidate: Spongebob Squarepants"
)
```
```
eval agent Spongebob Squarepants
Pretend to email: Hi Spongebob,

We at FoundationAI are building the future of AI by developing cutting-edge foundation models. We were very impressed with your academic achievements and your extensive experience in AI research, particularly in multi-agent systems and adaptive learning. Your expertise aligns perfectly with our focus on foundation model training.

We'd love to chat with you about how your skills could contribute to our mission. Are you available for a quick call next week?

Best,
Bob
FoundationAI
```
---

## Contributing

Contributions are welcome! Please feel free to submit a pull request or create an issue for feedback or feature requests.
