from pathlib import Path
import shlex
import subprocess
import os
from .lib.submissions_extraction import extract_submissions, clean_directory
import json
import importlib.util

from ...lib.helpers import GRADER_TYPES


GRADER_TYPE = GRADER_TYPES.UNITTEST
GRADER_VARIANT = "pytest"


def get_course_root(course):
    return Path(__file__).joinpath(
        f'../../../courses/{course}/app/').resolve()


def get_lab_path(course, lab):
    return get_course_root(course).joinpath(lab)


def get_course_year(course):
    course_path = get_course_root(course)
    spec = importlib.util.spec_from_file_location(
        "module.name", 
        course_path.joinpath('lib/app_config.py')
    )
    app_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_config)
    return app_config.YEAR


def run_grader(course, lab, runtime_limit):
    """
    Runs the tests in the given lab's corresponding pytest test file 
    which is test_run_grader.py in each lab directory  
    then saves the output in a file
    then pipes the pytest output file to console_log_parser 
    which will parse the pytest output to create 4 files
    1- [TIMESTAMP]_[LABNAME]_crash_details.txt which contains 
    detailed pytest output of only the failed tests for all the submissions
    2- [TIMESTAMP]_[LABNAME]_grade_summary.csv which contains
    the final grade of every submission
    3- [TIMESTAMP]_[LABNAME]_report.csv which also contains
    the grades but with specifiying which test passed and which didn't
    4- [TIMESTAMP]_[LABNAME]_short_crash_summary.txt which contains
    a summarized info about the failed tests for all submissions
    *(1) These files should be found inside {course_directory}/app/results/<YEAR>/{lab_name}
    after grading any lab of that course
    *(2) From GraderX point of view, results/ directory isn't used for anything, but there's a sibling res/
    directory which will contain one or more of these 4 files which will be fetched for download when requested
    """
    course_path = get_course_root(course)
    lab_path = get_lab_path(course, lab)
    lab_path_str = str(lab_path)
    student_tests_filter = ""
    # If "GRADERX_FJ" environment variable is set to "ENABLED"
    # run the tests with the firejail profile in the lab directory else run normally
    if student:
        student_tests_filter = "-m student"
    if ("GRADERX_FJ" in os.environ) and os.environ['GRADERX_FJ'] == "ENABLED":
        cmd = shlex.split(
            f"firejail --profile={lab_path_str}/firejail.profile pytest {student_tests_filter} -vv --tb=short --show-capture=no {lab_path_str}/test_run_grader.py")
    else:
        cmd = shlex.split(
            f"pytest {student_tests_filter} -vv --tb=short --show-capture=no {lab_path_str}/test_run_grader.py")
    file_name = "output.txt"
    with open(file_name, "w+") as f:
        subprocess.run(cmd, stdout=f)
    parser_file = "parser_output"
    # Gets the lab number from the lab name (whatever after "lab" in the lab name)
    # examples: lab3 has a lab_number (3), lab1_client has a lab_number (1_client)
    lab_number = lab.split('lab')[-1]
    with open(file_name, "r") as fi:
        with open(parser_file, "w+") as fo:
            # console_log_parser takes 2 command line arguements
            # the lab number and the (other) path to output files
            # To avoid confusion think of the files in res/ directory as the most recent grading output
            # and results/ directory as all the previously graded labs not only the most recent
            # the files in res/ are the ones that will be downloaded
            cmd = shlex.split(
                f"python {course_path}/lib/console_log_parser.py {lab_number} {course_path}/res")
            subprocess.run(cmd, stdin=fi, stdout=fo)


def add_submissions(course, lab, submissions_file):
    """
    Add submissions to the given lab, one of the possible "adding" methods is to extract the compressed 
    submissions_file in the [lab_path/submissions/<YEAR>] directory  
    """
    lab_path = get_lab_path(course, lab)
    lab_path_str = str(lab_path)
    extract_submissions(Path(
        f"{lab_path_str}/submissions/{get_course_year(course)}"), submissions_file)


def save_single_submission(course, lab, file_in_memory, filename):
    lab_path = get_lab_path(course, lab)
    lab_path.joinpath(f'submissions/{get_course_year(course)}/{filename}').write_bytes(
        file_in_memory.getbuffer())


def clear_submissions(course, lab):
    lab_path = get_lab_path(course, lab)
    clean_directory(lab_path.joinpath(f"submissions/{get_course_year(course)}"))


def results_to_download(course, lab):
    """
    Returns a list of files' Paths, these files could be one or more of the 4 files 
    mentioned in run_grader docstring. 
    """
    course_path = get_course_root(course)
    result_files_path = list(course_path.glob(f"res/{lab}*"))
    return result_files_path


# TODO: delete it
def get_diff_results_file(course_name, lab):
    path = Path("graderx").joinpath("graders").joinpath(
        "courses").joinpath(course_name).joinpath(lab)
    file_path = path.joinpath(f"{lab}_diff_result.json")
    with open(file_path) as f:
        data = json.load(f)
    return data


def get_submission_files(course, lab, submission_id):
    lab_path = get_lab_path(course, lab)
    return list(lab_path.glob(f"submissions/{get_course_year(course)}/{submission_id}.py"))


def update_submission_files(course, lab, submission_id, submission_files):
    submission_path = get_lab_path(course, lab).joinpath(f'submissions/{get_course_year(course)}/')
    for file_key in submission_files:
        submission_files[file_key].save(submission_path.joinpath(file_key))


def get_submission_file_content(course, lab, submission_id, file_name):
    submission_path = get_lab_path(course, lab).joinpath(f'submissions/{get_course_year(course)}/')
    submission_file = open(submission_path.joinpath(file_name))
    return submission_file.read()


def get_not_fullmark_submissions(course, lab):
    lab_path = get_lab_path(course, lab)
    submissions_path = lab_path.joinpath(f"submissions/{get_course_year(course)}")
    grades_file_path = get_course_root(course).joinpath(
        f'res/{lab}/{lab}_grade_summary.csv')
    with open(grades_file_path) as grades_file:
        not_fullmark_students_with_grades = grades_file.readlines()
    not_fullmark_students = []
    for student in not_fullmark_students_with_grades:
        if float(student.split(',')[1]) < 1:
            not_fullmark_students.append(student.split(',')[0])
    all_submissions_names = [
        sfile.name for sfile in submissions_path.glob('*.py')]
    not_fullmark_submissions = set()
    # TODO: Improve performance
    for student in not_fullmark_students:
        for submission_name in all_submissions_names:
            if student in submission_name:
                not_fullmark_submissions.add(
                    '.'.join(submission_name.split('.')[0:-1]))
    return list(not_fullmark_submissions)

def get_lab_guide_content(course, lab):
    lab_guide_path = get_lab_path(course, lab).joinpath('lab_guide.md')
    lab_guide = open(lab_guide_path)
    return lab_guide.read()
