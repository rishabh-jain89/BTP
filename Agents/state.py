from typing import TypedDict, List, Annotated
from sanboxed_environment.sandboxNode import runSandbox
import operator
import os
import json
import ollama
import yaml

class agentState(TypedDict):
    student_code: str
    test_inputs: List[str]
    execution_meta: dict
    next_node: str
    feedback_history: Annotated[List[dict], operator.add] 
    expected_outputs: dict

def load_data(state: agentState):
    code_path = '/home/dic/Desktop/Rishabh/BTP_Evaluation_Lab/Code/test.c'
    input_dir = '/home/dic/Desktop/Rishabh/BTP_Evaluation_Lab/inputs'
    expected_dir = '/home/dic/Desktop/Rishabh/BTP_Evaluation_Lab/expected'

    inputs = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir)])

    expected = {}
    for index, file in enumerate(sorted(os.listdir(expected_dir))):
        with open(os.path.join(expected_dir, file), 'r') as f:
            expected[f"Expected {index+1}"] = f.read()

    return {
        "student_code":code_path, 
        "test_inputs":inputs, 
        "next_node":"sandboxed_execution", 
        "expected_outputs":expected
    }


def sandbox_node(state:agentState):
    print("Running Sandbox Node")

    result = runSandbox(
        code_path = state["student_code"], 
        inputs = state["test_inputs"]
    )

    next = "logic_agent"

    for key, value in result.items():
        if value["exit_code"] != 0:
            next = "debugger_agent"
            break
    
    return {
        "execution_meta": result, 
        "next_node": next
    }

def debugger_node(state:agentState):
    results = state['execution_meta']
    with open(state['student_code'], 'r') as file:
        code = file.read()

    test_cases = {}
    for ind, test_path in enumerate(sorted(state['test_inputs'])):
        with open(test_path, 'r') as file:
            test_cases[f"Test Case {ind+1}"] = file.read()

    with open("/home/dic/Desktop/Rishabh/BTP_Evaluation_Lab/Agents/debugger.yaml", "r") as file:
        agent = yaml.safe_load(file)

    template = agent["debugger-agent"]["prompt"]
    prompt = template.format(
        student_code = code,
        sandbox_results = results,
        test_cases = test_cases
    )

    response = ollama.generate(
        model = 'llama3.1:8b', 
        format = 'json',
        prompt = prompt
    )

    return {
        "debugger": response['response'], 
        "next_node": "logic_agent"
    }

initial_state = {
    "student_code": "", 
    "test_inputs":[], 
    "expected_outputs":{},  
    "next_node":"", 
    "execution_meta": {},
    "feedback_history": []
}

print("Loading the data")
state = load_data(initial_state) # Here we are initializing the Agent state and loading the basic data

sandbox_output = sandbox_node(state) # Here the Sandbox node is getting executed 

state['execution_meta'] = sandbox_output['execution_meta']
state['next_node'] = sandbox_output['next_node']

debugger_response = debugger_node(state) # Here the debugger node is executed

state['debugger'] = json.loads(debugger_response['debugger']) # debugger response adding in state
state['next_node'] = debugger_response['next_node']

json_final_state = json.dumps(state, indent=4)

print("Final State:", json_final_state)