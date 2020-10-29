import sys
import os
import shlex
import subprocess
import difflib
from pathlib import Path
from .lib import compile_submission as compiler
from .lib import compute_results as compute_results
from .lib import test_cases_parser as tc_parser
from .lib.submissions_extraction import extract_submissions, clean_directory
from ...lib import helpers
import json


def get_lab_path(course, lab):
    return Path(__file__).joinpath(
        f'../../../courses/{course}/labs/{lab}').resolve()


def run_grader(course, lab, key, public_testcases = None):
    """
    Compiles all the submissions in [lab_path/submissions/] directory, runs compiled submissions
    with stdin of the lab's test cases, then builds a dictionary that has all the submissions 
    with the submissions id as the key and the results of this submissions as the value 
    example dictionray:
    {
        "3245_3213": {
            "passed": [1, 3, 5 , 7],
            "failed": [
                {"tc_id": "2", "diff": *DIFF TEXT*}, 
                {"tc_id": "4", "diff": *DIFF TEXT*}, 
                {"tc_id": "6", "diff": *DIFF TEXT*}]
        },
        "2136_2315": {
            "passed": [1, 2, 3, 5, 6, 7],
            "failed": [
                {"tc_id": "4", "diff": *DIFF TEXT*}, 
        }
    }
    """
    LAB_ABS_PATH = get_lab_path(course, lab)
    test_cases = tc_parser.get_test_cases(LAB_ABS_PATH, public_testcases)
    submission_result_list = []

    # Looping over all the submissions in [lab_path/submissions/] directory, first compile the submission
    # then loop over all test_cases for this lab, run the compiled submissions with stdin of the test case input
    # then compare it to the test case output, if both matched add the test case id to the "passed" array
    # if not add the test case id along with the diff between outout and test case expected output to "failed" array
    for _, dir, _ in os.walk(LAB_ABS_PATH.joinpath(f"submissions/{key}")):
        for i in dir:
            submission_dir = str(
                LAB_ABS_PATH.joinpath(f"submissions/{key}")) + f"/{i}"
            compiler.compile_submission(Path(submission_dir))

            current_submission = {
                "id": i,
                "passed": [],
                "failed": []
            }
            for tc in test_cases:
                exec_command = f"./a.out"
                cmd = shlex.split(exec_command)
                cprocess = subprocess.run(
                    cmd, input=tc[1], cwd=submission_dir, capture_output=True, text=True)
                differences = ""
                for line in difflib.context_diff(cprocess.stdout, tc[2]):
                    differences += line + "\n"
                if(len(differences) == 0):
                   current_submission["passed"].append(tc[0])
                else:
                    student_output = ""
                    if cprocess.returncode != 0:
                        student_output = "ERROR"
                    else:
                        student_output = cprocess.stdout
                    current_submission["failed"].append({
                        "tc_id": tc[0],
                        "output": student_output,
                        "expected": tc[2]
                    })
            submission_result_list.append(current_submission)
                
    # compute_total_result will take the results dict then create results files in the lab's directory
    compute_results.compute_total_result(submission_result_list, LAB_ABS_PATH, key)


def add_submissions(course, lab, submissions_file):
    """
    Add submissions to the given lab, one of the possible "adding" methods is to extract the compressed 
    submissions_file in the [lab_path/submissions/] directory  
    """
    lab_path = get_lab_path(course, lab)
    timestamp = helpers.current_timestamp()
    # extract_submissions will clean the target submissions directory before extracting
    extract_submissions(lab_path.joinpath(f'submissions/{timestamp}'), submissions_file)
    return timestamp


# TODO: This function doesn't fit c grader since its submissions are directories not files
def save_single_submission(course, lab, file_in_memory, filename, submission_key):
    lab_path = get_lab_path(course, lab)
    submission_path = lab_path.joinpath(f'submissions/{submission_key}')
    if not submission_path.exists():
        submission_path.mkdir(parents=True)
    submission_path.joinpath(f'{filename}').write_bytes(
        file_in_memory.getbuffer())


def clear_submissions(course, lab):
    lab_path = get_lab_path(course, lab)
    clean_directory(lab_path.joinpath('submissions'))


def results_to_download(course, lab, key):
    """
    Returns a list of files Paths, these files could be result files, crash logs or whatever files
    that have information about the grading process. 
    """
    lab_path = get_lab_path(course, lab)
    return list(lab_path.glob(f"/submissions/{key}/**/*_results.txt")) + list(lab_path.glob(f"/submissions/{key}/**/*_result_summary.txt"))


def get_diff_results_file(course_name, lab, key):
    path = Path("graderx").joinpath("graders").joinpath(
        "courses").joinpath(course_name).joinpath("labs").joinpath(lab)
    lab_path = get_lab_path(course_name, lab)
    file_path = lab_path.joinpath(f"/submissions/{key}/{lab}_diff_result.json")
    with open(file_path) as f:
        data = json.load(f)
    return data

def get_submission_files(course, lab, submission_id, submission_key):
    lab_path = get_lab_path(course, lab)
    return list(lab_path.glob(f"submissions/{submission_key}/{submission_id}/*.c"))

def update_submission_files(course, lab, submission_id, submission_files, submission_key):
    submission_path = get_lab_path(course, lab).joinpath(f'submissions/{submission_key}/{submission_id}')
    for file_key in submission_files:
        submission_files[file_key].save(submission_path.joinpath(file_key))

def get_submission_file_content(course, lab, submission_id, file_name, submission_key):
    submission_path = get_lab_path(course, lab).joinpath(f'submissions/{submission_key}/{submission_id}')
    submission_file = open(submission_path.joinpath(file_name))
    return submission_file.read()

def get_not_fullmark_submissions(course, lab, submission_key):
    lab_path = get_lab_path(course, lab)
    file_path = lab_path.joinpath(f"submissions/{submission_key}/{lab}_diff_result.json")
    with open(file_path) as diff_file:
        diff_dict = json.load(diff_file)
    return [submission['id'] for submission in diff_dict]
