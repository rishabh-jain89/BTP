import docker
import signal
import os
import io
import tarfile
from typing import List

STUDENT_OUTPUT_FILE = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/output/output.txt'

if os.path.exists(STUDENT_OUTPUT_FILE):
    os.remove(STUDENT_OUTPUT_FILE)

class TimeoutError(Exception):
    pass

def timeoutHandler(signum, frame):
    raise TimeoutError("Function call timed out")

def readFromContainer(container, path):
    stream, _ = container.get_archive(path)
    file = io.BytesIO(b''.join(stream))
    with tarfile.open(fileobj=file) as tar:
        member = tar.getmembers()[0]
        f = tar.extractfile(member)
        return f.read().decode() if f else ""

def runSandbox(code_path:str, inputs:List[str]) -> dict:
    client = docker.from_env()
    output = {}

    for index, test_path in enumerate(inputs):

        # This is the docker container configuration 
        container = client.containers.create(
                image = "gcc-sandbox:latest",
                command = ["sh", "-c","gcc /app/main.c -o program 2> /app/stderr.txt&& ./program < /app/test.txt > /app/stdout.txt 2>> /app/stderr.txt"], 
                mem_limit = '128m', 
                nano_cpus = 1000000000, 
                volumes= {
                    code_path: {
                        'bind':'/app/main.c', 
                        'mode':'ro'
                    },
                    test_path: {
                        'bind':'/app/test.txt', 
                        'mode':'ro'
                    }
                }, 
                log_config={
                    'Type':'json-file', 
                    'Config':{
                        'max-size':'1m',
                        'max-file':'1'
                    }
                }
            )
        
        try:
            signal.signal(signal.SIGALRM, timeoutHandler)
            signal.alarm(5)
            container.start()
            result = container.wait()
            logs = container.logs()
            stdout_content = readFromContainer(container, '/app/stdout.txt')
            stderr_content = readFromContainer(container, '/app/stderr.txt')
            output[f"test case {index+1}"] = {
                "status":"success", 
                "exit_code":result.get('StatusCode', 1), 
                "stdout": stdout_content, 
                "stderr": stderr_content
            }
            print("Successfull Execution, Output:", logs.decode())
        except docker.errors.ContainerError as e:
            output[f"test case {index+1}"] = {
                "status":"failed", 
                "exit_code": e.exit_status,
                "stdout": "", 
                "stderr": "Execution Failed"
            }
            print("Execution Failed!")
            print("Exit Code:", e.exit_status)
            print("Error Message:", e.stderr.decode())
        except TimeoutError as e:
            output[f"test case {index+1}"] = {
                "status":"failed", 
                "exit_code": -1, 
                "stdout": "", 
                "stderr": "Infinite Loop Detected"
            }
            print(f"Timeout Error: Program took too long to execute")
        except Exception as e:
            output[f"test case {index+1}"] = {
                "status":"failed", 
                "exit_code":e.exit_status, 
                "stdout": "", 
                "stderr": f"A new exception encountered:{e}"
            }
            print("A new exception encountered:", e)
        finally:
            signal.alarm(0)
            if container.status == 'running':
                container.kill()
            container.remove(force=True)

    with open(STUDENT_OUTPUT_FILE, 'w') as file:
        for key, value in output.items():
            file.write(f"{value['stdout']}\n")

    return output