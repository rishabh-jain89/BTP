from typing import TypedDict, List, Annotated
import operator
import os
import json
from sanboxed_environment.sandboxNode import runSandbox

class agentState(TypedDict):
    student_code: str
    test_inputs: List[str]
    execution_meta: dict
    next_node: str
    feedback_history: Annotated[List[str], operator.add] 
    expected_outputs:str

def load_data(state: agentState):
    code_path = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/Code/test.c'
    input_dir = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/inputs'
    expected_dir = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/expected'

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

initial_state = {
    "student_code": "", 
    "test_inputs":[], 
    "expected_outputs":{}, 
    "execution_meta":{}, 
    "next_node":"", 
    "feedback_history":[]
}

print("Loading the data")
loaded_state = load_data(initial_state)

sandbox_output = sandbox_node(loaded_state)

final_state = loaded_state | sandbox_output

json_final_state = json.dumps(final_state, indent=4)

print("Final State:", json_final_state)