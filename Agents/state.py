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
    code_path = 'Code/test.c'
    input_dir = 'inputs'
    expected_dir = 'expected'
    assignment_path = 'Assignment/assignment.txt'

    inputs = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir)])

    expected = {}
    for index, file in enumerate(sorted(os.listdir(expected_dir))):
        with open(os.path.join(expected_dir, file), 'r') as f:
            expected[f"Expected {index+1}"] = f.read()

    with open(assignment_path, 'r') as file:
        assignment = file.read()

    with open(code_path, 'r') as file:
        code = file.read()

    return {
        "student_code":code,
        "student_code_path": code_path,
        "test_inputs":inputs, 
        "next_node":"sandboxed_execution", 
        "expected_outputs":expected, 
        "problem_statement": assignment
    }

def sandbox_node(state:agentState):
    print("Running Sandbox Node")

    result = runSandbox(
        code_path = state["student_code_path"], 
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
    code = state['student_code']

    test_cases = {}
    for ind, test_path in enumerate(sorted(state['test_inputs'])):
        with open(test_path, 'r') as file:
            test_cases[f"Test Case {ind+1}"] = file.read()

    with open("Agents/debugger.yaml", "r") as file:
        agent = yaml.safe_load(file)

    template = agent["debugger-agent"]["prompt"]
    model = agent['debugger-agent']['model']
    prompt = template.format(
        student_code = code,
        sandbox_results = results,
        test_cases = test_cases
    )

    response = ollama.generate(
        model = model, 
        format = 'json',
        prompt = prompt, 
        options = {
            "temperature": 0.1
        }
    )

    return {
        "debugger": response['response']
    }

def logic_node(state:agentState):
    assignment = state['problem_statement']
    code = state['student_code']
    actual_output = state['execution_meta']
    expected_output = state['expected_outputs']

    with open("Agents/logic.yaml", 'r') as file:
        agent = yaml.safe_load(file)
    
    template = agent['logic_agent']['prompt']
    model = agent['logic_agent']['model']
    prompt = template.format(
        assignment = assignment, 
        student_code = code,
        actual_output = actual_output,
        expected_output = expected_output
    )

    response = ollama.generate(
        model = model, 
        format = 'json', 
        prompt = prompt, 
        options = {
            "temperature": 0.1
        }
    )

    try:
        logic_result = json.loads(response['response'])
    except:
        print("Failed to load the logic agent response")

    return {
        "logic_agent": logic_result
    }

def quality_node(state: agentState):
    code = state['student_code']

    with open('Agents/quality.yaml', 'r') as file:
        agent = yaml.safe_load(file)

    template = agent['quality_agent']['prompt']
    model = agent['quality_agent']['model']
    prompt = template.format(
        student_code = code
    )

    response = ollama.generate(
        model = model,
        format = 'json', 
        prompt = prompt, 
        options = {
            "temperature": 0.1
        }
    )

    try:
        quality_result = json.loads(response['response'])
    except:
        print("Failed to load the quality agent response")

    return {
        "quality": quality_result
    }

def grader_node(state: agentState):
    assignment = state['problem_statement']
    debugger_report = state['debugger_report']
    logic_report = state['logic_report']
    quality_report = state['quality_report']
    total = 10

    with open('Agents/grader.yaml', 'r') as file:
        agent = yaml.safe_load(file)

    template = agent['grader_agent']['prompt']
    model = agent['grader_agent']['model']
    prompt = template.format(
        assignment = assignment, 
        debugger_report = debugger_report, 
        logic_report = logic_report, 
        quality_report = quality_report, 
        total_marks = total 
    )

    response = ollama.generate(
        model = model, 
        format = 'json', 
        prompt = prompt, 
        options = {
            "temperature": 0.1
        }
    )

    try:
        grader_report = json.loads(response['response'])
    except:
        print("Failed to load the Grader agent response")

    return {
        "grader_report": grader_report
    }

initial_state = {
    "student_code": "", 
    "test_inputs":[], 
    "expected_outputs":{},  
    "next_node":"", 
    "execution_meta": {},
    "feedback_history": [],
    "problem_statement": ""
}

print("Loading the data")
state = load_data(initial_state) # Here we are initializing the Agent state and loading the basic data

sandbox_output = sandbox_node(state) # Here the Sandbox node is getting executed 

state['execution_meta'] = sandbox_output['execution_meta']
state['next_node'] = sandbox_output['next_node']

debugger_response = {}
if state['next_node'] == "debugger_agent":
    debugger_response = debugger_node(state) # Here the debugger node is executed
    state['debugger_report'] = json.loads(debugger_response) # debugger response adding in state
else:
    state['debugger_report'] = "No technical Errors detected"

state['next_node'] = 'logic_agent'

logic_node_response = logic_node(state)

state["logic_report"] = logic_node_response["logic_agent"]
state["next_node"] = "quality agent"

quality_node_response = quality_node(state)
state["quality_report"] = quality_node_response["quality"]
state['next'] = "grader_agent"

grader_node_response = grader_node(state)

state['grader_report'] = grader_node_response['grader_report']
state['next'] = 'end'

json_final_state = json.dumps(state, indent=4)

print("Final State:", json_final_state)