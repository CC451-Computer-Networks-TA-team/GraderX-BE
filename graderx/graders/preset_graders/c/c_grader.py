import sys
import os
from pathlib import Path
import lib.compile_submission as compiler

COURSE_ABS_PATH = None
LAB_ABS_PATH = None


def main():
    """
    Example compile_submission usage
    try:
        compiler.compile_submission(
            LAB_ABS_PATH.joinpath("submissions/3645_5436"))
    except compiler.CompilationFailedError as e:
        print(e)
    """
    test_cases_count = submissions_count = 0
    for _, dirnames, filenames in os.walk(LAB_ABS_PATH.joinpath(f"submissions")):
        submissions_count += len(dirnames)
        break
    
    for _, dirnames, filenames in os.walk(LAB_ABS_PATH.joinpath(f"test_cases")):
        test_cases_count += len(filenames)
        break

    test_cases_count = int(test_cases_count / 2)
    print(submissions_count)
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
