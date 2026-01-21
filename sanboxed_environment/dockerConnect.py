import docker
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function call timed out")

client = docker.from_env()

# This is the docker container configuration 
container = client.containers.create(
        image = "gcc-sandbox:latest",
        command = ["sh", "-c","gcc /app/main.c -o program && ./program"], 
        mem_limit = '128m', 
        nano_cpus = 1000000000, 
        volumes= {
            '/home/rishabh-yoga/Desktop/Sem 6/Project/BTP_Evaluation_Lab/sanboxed_environment/test.c':{
                'bind':'/app/main.c', 
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
    print("Successfull Execution, Output:", logs.decode())
except docker.errors.ContainerError as e:
    print("Execution Failed!")
    print("Exit Code:", e.exit_status)
    print("Error Message:", e.stderr.decode())
except TimeoutError as e:
    print(f"Timeout Error: Program took too long to execute{e}")
except Exception as e:
    print("A new exception encountered:", e)
finally:
    signal.alarm(0)
    if container.status == 'running':
        container.kill()
    container.remove()
    