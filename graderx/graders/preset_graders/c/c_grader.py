import sys
import os
import shlex
import subprocess
from pathlib import Path
import lib.compile_submission as compiler

COURSE_ABS_PATH = None
LAB_ABS_PATH = None

test_cases = [
    ("1", "Hello\nWorld\n", "HelloWorld\n"),
    ("2", "Hakuna\nMatata\n", "HakunaMatata\n"),
    ("3", "First\nSecond\n", "FirstSecond\n"),
    ("4", "Fizz\nBuzz\n", "FizzBuzz\n"),
    ("5", "Sneaky \nTestCase\n", "Sneaky TestCase\n")
]

def main():
    """
    Example compile_submission usage
    try:
        compiler.compile_submission(
            LAB_ABS_PATH.joinpath("submissions/3645_5436"))
    except compiler.CompilationFailedError as e:
        print(e)
    """
    
    for _, dir, _ in os.walk(LAB_ABS_PATH.joinpath(f"submissions")):
        for i in dir:
            s = str(LAB_ABS_PATH.joinpath(f"submissions")) + f"/{i}"
            compiler.compile_submission(Path(s))
            s = "./a.out"
            cmd = shlex.split(["./a.out", ])
            cprocess = subprocess.run(
            cmd, cwd=Path(s), capture_output=True, text=True)
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
