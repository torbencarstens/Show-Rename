import subprocess
from typing import List, Tuple, Dict

BINARY = "mkvpropedit"


def set_attributes(filename: str, items: List[Tuple[str, str]]) -> List[Tuple[str, bool]]:
    results = []

    for item in items:
        result = set_attribute(filename, item[0], item[1])
        results.append(("=".join([item[0], item[1]]), result))

    return results


def set_attribute(filename: str, key: str, value: str) -> bool:
    result = run(["-s", "=".join([key, value]), filename])

    return determine_success_from_output(result)


def set_title(filename: str, value: str) -> bool:
    return set_attribute(filename, "title", value)


def run(args: List[str]) -> Dict[str, any]:
    process = subprocess.Popen([BINARY] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    returncode = process.returncode

    stdout = stdout.decode("UTF-8")
    stderr = stderr.decode("UTF-8")
    if len(stdout) == 0:
        stdout = None
    if len(stderr) == 0:
        stderr = None

    return {
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr
    }


def determine_success_from_output(output: Dict[str, any]) -> bool:
    return output.get("returncode", -1) == 0 and \
           output.get("stderr", "no stderr found") is None and \
           "Done" in output.get("stdout", "no stdout")
