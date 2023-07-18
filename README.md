# Prompt-Promptor

Prompt-Promptor(or shorten for ppromptor) is a Python library with a with web interface that automatically generates and improves prompts for LLMs. It adapts concepts from autonomous agents (e.g., AutoGPT), and comprises three agents: Proposer, Evaluator, and Analyzer. These agents work together to continuously improve the generated prompts.

## Features:

1. 🤖 The use of powerful LLMs (eg, GPT4) to analyze and generate prompts for less-powerful LLMs(eg, Llama).

2. 👨‍👨‍👧‍👦 Collaboration with human experts.

3. 💼 Prompt experiment management.


## Installations

### From Github
1. Clone Repository from Github
```
git clone https://github.com/pikho/ppromptor.git
cd ppromptor
```

2. Install Required Packages
```
pip install -r requirements.txt
```

3. Add Package Path to PythonPath
```
export PYTHONPATH=PYTHONPATH:<path_to_repo>/ppromptor
```

4. Run Tests
```
pip install -r requirements_test.txt

pytest
```

### Running Local Model(WizardLM)
1. Install Required Packages
```
pip install requirements_local_model.txt
```

2. Test if WizardLM can run correctly
```
cd <path_to_ppromptor>/ppromptor/llms
python wizardlm.py
```

Rewrite below article in formal English


## Usages

1. Start Web App
```
cd <path_to_ppromptor>
streamlit streamlit run ui/app.py
```

2. Load Demo Project
Load `examples/antonyms.db` for demo purpose. This demostrate how to guide WizardLM to generate antonyms for given inputs.

3. Configuration
In Configuration page, set `Target LLM` as `wizardlm` if you can infer this model locally. Or choose both `Target LLM` and `Analysis LLM` as `chatgpt`. If chatgpt is used, please provide OpenAI API Key.

4. Load dataset
The demo project already loaded 5 records. You can add your own dataset.

5. Start Wordload
Press `Start` button to activate the workflow.

5. Prompt Candidates
Generated prompts can be found in `Prompt Candidates` tab. Users can modify generated prompts by selecting only 1 Prompt Candidate, then modifying the prompt, then `Create Prompt`. By selecting 2 prompts, we can compare these prompts side by side.



## Usage

1. Start the Web App
```
cd <path_to_ppromptor>
streamlit run ui/app.py
```

2. Load the Demo Project
Load `examples/antonyms.db`(default) for demo purposes. This demonstrates how to use ChatGPT to guide WizardLM to generate antonyms for given inputs.

3. Configuration
In the Configuration tab, set `Target LLM` as `wizardlm` if you can infer this model locally. Or choose both `Target LLM` and `Analysis LLM` as `chatgpt`. If chatgpt is used, please provide the OpenAI API Key.

4. Load the dataset
The demo project has already loaded 5 records. You can add your own dataset.(Optional)

5. Start the Workload
Press the `Start` button to activate the workflow.

5. Prompt Candidates
Generated prompts can be found in the `Prompt Candidates` tab. Users can modify generated prompts by selecting only 1 Candidate, then modifying the prompt, then `Create Prompt`. This new prompt will be evaluated by Evaluator agent and then keep improving by Analyzer agent. By selecting 2 prompts, we can compare these prompts side by side.

![Compare Prompts](https://github.com/pikho/ppromptor/blob/main/doc/images/cmp_candidates-2.png?raw=true)

