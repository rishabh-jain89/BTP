import docker
import signal
import os

INPUT_DIRECTORY_PATH = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/inputs'
STUDENT_OUTPUT_FILE = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/output/output.txt'
STUDENT_PROGRAM_PATH = '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/Code'

if os.path.exists(STUDENT_OUTPUT_FILE):
    os.remove(STUDENT_OUTPUT_FILE)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function call timed out")

client = docker.from_env()

for index, test in enumerate(sorted(os.listdir(INPUT_DIRECTORY_PATH))):
    test_path = os.path.join(INPUT_DIRECTORY_PATH, test)
    for code in os.listdir(STUDENT_PROGRAM_PATH):
        code_path = os.path.join(STUDENT_PROGRAM_PATH, code)

    # This is the docker container configuration 
    container = client.containers.create(
            image = "gcc-sandbox:latest",
            command = ["sh", "-c","gcc /app/main.c -o program && ./program < /app/test.txt"], 
            mem_limit = '128m', 
            nano_cpus = 1000000000, 
            volumes= {
                code_path:{
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
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        container.start()
        result = container.wait()
        logs = container.logs()
        with open(STUDENT_OUTPUT_FILE, 'a') as output_file:
            output_file.write(f"{logs.decode()}\n")
        print("Successfull Execution, Output:", logs.decode())
    except docker.errors.ContainerError as e:
        with open(STUDENT_OUTPUT_FILE, 'a') as output_file:
            output_file.write("Execution Failed\n")
        print("Execution Failed!")
        print("Exit Code:", e.exit_status)
        print("Error Message:", e.stderr.decode())
    except TimeoutError as e:
        with open(STUDENT_OUTPUT_FILE, 'a') as output_file:
            output_file.write("Infinite Loop Detected\n")
        print(f"Timeout Error: Program took too long to execute{e}")
    except Exception as e:
        with open(STUDENT_OUTPUT_FILE, 'a') as output_file:
            output_file.write(f"A new exception encountered:{e}\n")
        print("A new exception encountered:", e)
    finally:
        signal.alarm(0)
        if container.status == 'running':
            container.kill()
        container.remove(force=True)
