from __future__ import annotations

import io
import os
import tarfile
from typing import Any

import docker


DEFAULT_TIMEOUT_SECONDS = 5


def read_from_container(container, path: str) -> str:
    stream, _ = container.get_archive(path)
    file_obj = io.BytesIO(b"".join(stream))

    with tarfile.open(fileobj=file_obj) as tar:
        members = tar.getmembers()
        if not members:
            return ""

        extracted = tar.extractfile(members[0])
        if extracted is None:
            return ""

        return extracted.read().decode("utf-8", errors="replace")


def get_output_file_path() -> str:
    workspace_dir = os.environ.get("WORKSPACE_DIR")
    if workspace_dir:
        output_dir = os.path.join(workspace_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, "output.txt")

    os.makedirs("output", exist_ok=True)
    return os.path.join("output", "output.txt")


def _build_failure_result(message: str, exit_code: int = 1) -> dict[str, Any]:
    return {
        "status": "failed",
        "exit_code": exit_code,
        "stdout": "",
        "stderr": message,
    }


def runSandbox(code_path: str, inputs: list[str]) -> dict[str, dict[str, Any]]:
    client = docker.from_env()
    output: dict[str, dict[str, Any]] = {}

    abs_code_path = os.path.abspath(code_path)

    try:
        for index, test_path in enumerate(inputs, start=1):
            abs_test_path = os.path.abspath(test_path)
            container = None
            stdout_content = ""
            stderr_content = ""
            exit_code = 1

            test_key = f"test case {index}"

            try:
                container = client.containers.create(
                    image="gcc-sandbox:latest",
                    command=[
                        "sh",
                        "-c",
                        (
                            "touch /app/stdout.txt && "
                            "touch /app/stderr.txt && "
                            "gcc /app/main.c -o program 2>> /app/stderr.txt && "
                            "./program < /app/test.txt >> /app/stdout.txt 2>> /app/stderr.txt"
                        ),
                    ],
                    mem_limit="128m",
                    nano_cpus=1000000000,
                    volumes={
                        abs_code_path: {
                            "bind": "/app/main.c",
                            "mode": "ro",
                        },
                        abs_test_path: {
                            "bind": "/app/test.txt",
                            "mode": "ro",
                        },
                    },
                    log_config={
                        "Type": "json-file",
                        "Config": {
                            "max-size": "1m",
                            "max-file": "1",
                        },
                    },
                )

                container.start()
                result = container.wait(timeout=DEFAULT_TIMEOUT_SECONDS)

                stdout_content = read_from_container(container, "/app/stdout.txt")
                stderr_content = read_from_container(container, "/app/stderr.txt")

                exit_code = result.get("StatusCode", 1)
                output[test_key] = {
                    "status": "success" if exit_code == 0 else "failed",
                    "exit_code": exit_code,
                    "stdout": stdout_content,
                    "stderr": stderr_content,
                }

            except docker.errors.APIError as exc:
                output[test_key] = _build_failure_result(f"Docker API error: {exc}")
            except Exception as exc:
                output[test_key] = _build_failure_result(f"Sandbox execution error: {exc}", exit_code)
            finally:
                if container is not None:
                    try:
                        container.reload()
                        if container.status == "running":
                            container.kill()
                    except Exception:
                        pass

                    try:
                        container.remove(force=True)
                    except Exception:
                        pass

        student_output_file = get_output_file_path()
        with open(student_output_file, "w", encoding="utf-8") as file_obj:
            for result in output.values():
                file_obj.write(f"{result['stdout']}\n")

        return output

    finally:
        try:
            client.close()
        except Exception:
            pass