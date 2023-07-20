import textwrap
from typing import Dict, Optional, Union

from langchain.prompts import PromptTemplate
from loguru import logger


def get_llm_params(llm) -> Dict:
    res = {}
    res["llm_name"] = llm.__class__.__name__
    res.update(llm._default_params)
    return res


def bulletpointize(lst):
    res = []
    for idx, v in enumerate(lst):
        res.append(f"{str(idx+1)}. {v}")
    return res


def evaluate_guideline_contribution(evaluator,
                                    dataset,
                                    prompt,
                                    guidelines,
                                    llm):
    for idx in range(len(guidelines)):
        gl = guidelines[:]
        del gl[idx]
        logger.debug(f"Removed guideline idenx: {idx}")
        evaluator.eval(dataset, prompt, gl, llm)


def gen_prompt(goal: Union[str, PromptTemplate],
               instrutions: Union[str, PromptTemplate],
               guidelines: Optional[Union[str, PromptTemplate, list]] = None,
               examples: Optional[Union[str, PromptTemplate]] = None,
               input_variables: Optional[list] = None):

    if input_variables is None:
        input_variables = []

    if isinstance(goal, str):
        goal = PromptTemplate(template=goal, input_variables=[])

    if isinstance(instrutions, str):
        instrutions = PromptTemplate(template=instrutions, input_variables=[])

    if (guidelines is None) or (isinstance(guidelines, list) and len(guidelines) == 0):
        guidelines = PromptTemplate(template="\n", input_variables=[])
    elif isinstance(guidelines, list):
        _gls = "\nGuidelines:\n" + "\n".join(bulletpointize(guidelines))
        guidelines = PromptTemplate(template=_gls, input_variables=[])
    elif isinstance(guidelines, str):
        guidelines = PromptTemplate(template=guidelines, input_variables=[])

    if (examples is None) or (isinstance(examples, list) and len(examples) == 0):
        examples = "\n"
    elif isinstance(examples, list):
        _exs = "Examples:\n" + "\n".join(bulletpointize(examples))
        examples = PromptTemplate(template=_exs, input_variables=[])
    elif isinstance(examples, str):
        examples = PromptTemplate(template=examples, input_variables=[])

    components = [goal, guidelines, examples, instrutions]
    prompt_str = "\n".join([textwrap.dedent(x.template) for x in components])  # type: ignore[union-attr]

    for component in components:
        for i in component.input_variables:  # type: ignore[union-attr]
            assert i not in input_variables
            input_variables.append(i)

    return PromptTemplate(template=prompt_str,
                          input_variables=input_variables)


def load_lm(name):
    if name == "mlego_wizardlm":
        from ppromptor._private_llms.mlego_llm import WizardLLM

        return WizardLLM()
    elif name == "wizardlm":
        from ppromptor.llms.wizardlm import WizardLLM

        return WizardLLM()
    elif name == "chatgpt":
        from langchain.chat_models import ChatOpenAI

        return ChatOpenAI(model_name='gpt-3.5-turbo',
                          temperature=0.1)
