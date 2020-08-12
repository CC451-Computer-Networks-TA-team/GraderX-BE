import sys
import os
import shlex
import subprocess
import difflib
from pathlib import Path
import lib.compile_submission as compiler
from lib import compute_results as compute_results

COURSE_ABS_PATH = None
LAB_ABS_PATH = None

test_cases = [
    ("1", "Hello\nWorld\n", "HelloWorld\n"),
    ("2", "Hakuna\nMatata\n", "HakunaMatata\n"),
    ("3", "First\nSecond\n", "FirstSecond\n"),
    ("4", "Fizz\nBuzz\n", "FizzBuzz\n"),
    ("5", "Sneaky \nTestCase\n", "Sneaky TestCase\n")
]

submission_result_dict = {}

def main():
    
    for _, dir, _ in os.walk(LAB_ABS_PATH.joinpath(f"submissions")):
        for i in dir:
            global submission_result_dict
            submission_dir = str(LAB_ABS_PATH.joinpath(f"submissions")) + f"/{i}"
            compiler.compile_submission(Path(submission_dir))
            submission_result_dict[i] = {
                "passed": [],
                "failed": []
            }
            for tc in test_cases:
                exec_command = f"./a.out"
                cmd = shlex.split(exec_command)
                cprocess = subprocess.run(
                    cmd, input=tc[1] ,cwd=submission_dir, capture_output=True, text=True)
                differences = ""
                for line in difflib.context_diff(cprocess.stdout, tc[2]):
                    differences += line + "\n"
                if(len(differences) == 0) :
                    submission_result_dict[i]["passed"].append(tc[0])
                else:
                    submission_result_dict[i]["failed"].append({
                        "tc_id": tc[0],
                        "diff": differences
                    })

    compute_results.compute_total_result(submission_result_dict, LAB_ABS_PATH)
    pass


if __name__ == "__main__":
    try:
        COURSE_ABS_PATH = Path(__file__).joinpath(
            f'../../../courses/{sys.argv[1]}').resolve()
        LAB_ABS_PATH = COURSE_ABS_PATH.joinpath(f"labs/{sys.argv[2]}")
    except IndexError:
        print("""
        [WARNING]: Please provide a course and lab as arguements
        ex: $python c_grader.py test_course lab1
        Running with default arguements [ test_course lab1 ]
        """)
        COURSE_ABS_PATH = Path(__file__).joinpath(
            f'../../../courses/test_course').resolve()
        LAB_ABS_PATH = COURSE_ABS_PATH.joinpath(f"labs/lab1")
    main()
