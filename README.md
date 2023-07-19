# Prompt-Promptor: An Autonomous Agent for Prompt Engineering

Prompt-Promptor(or shorten for ppromptor) is a Python library designed to automatically generate and improve prompts for LLMs. It draws inspiration from autonomous agents like AutoGPT and consists of three agents: Proposer, Evaluator, and Analyzer. These agents work together with human experts to continuously improve the generated prompts.

## 🚀 Features:

- 🤖 The use of LLMs to prompt themself by giving few samples.

- 💪 Guidance for OSS LLMs(eg, LLaMA) by more powerful LLMs(eg, GPT4)

- 📈 Continuously improvement.

- 👨‍👨‍👧‍👦 Collaboration with human experts.

- 💼 Experiment management for prompt engineering.

- 🖼 Web GUI interface.

- 🏳️‍🌈 Open Source.

## Warning
- This project is currently in its earily stage, and it is anticipated that there will be major design changes in the future.

- The main function utilizes an infinite loop to enhance the generation of prompts. If you opt for OpenAI's ChatGPT as Target/Analysis LLMs, kindly ensure that you set a usage limit.

## Concept

![Compare Prompts](https://github.com/pikho/ppromptor/blob/main/doc/images/concept.png?raw=true)

A more detailed class diagram could be found in [doc](https://github.com/pikho/ppromptor/tree/main/doc)

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

![Compare Prompts](https://github.com/pikho/ppromptor/blob/main/doc/images/cmp_candidates-1.png?raw=true)

![Compare Prompts](https://github.com/pikho/ppromptor/blob/main/doc/images/cmp_candidates-2.png?raw=true)

## Contribution
We welcome all kinds of contributions, including new feature requests, bug fixes, new feature implementation, examples, and documentation updates. If you have a specific request, please use the "Issues" section. For other contributions, simply create a pull request (PR). Your participation is highly valued in improving our project. Thank you!