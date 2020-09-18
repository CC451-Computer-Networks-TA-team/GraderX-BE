import json
from .stdout_graders.c import c_grader
from .unittest_graders.pytest import pytest_grader
from pathlib import Path
from .lib import helpers
import os
from .moss import moss
from .stdout_graders.c.lib import submissions_extraction

def get_courses_config():
    """
    Creates a dict out of courses_config json file then returns it
    """
    with open(Path(__file__).parent.joinpath("courses_config.json")) as f:
        return json.load(f)


def get_courses():
    return list(get_courses_config().keys())


def get_labs(course_name):
    return get_courses_config()[course_name]['labs']


def select_course_grader(course_name):
    """
    Finds the grader responsible for the given course then returns its main module
    """
    course_config = get_courses_config()[course_name]
    if course_config['type'] == "stdout":
        if course_config['variant'] == "c":
            return c_grader
        else:
            raise InvalidConfigError()
    elif course_config['type'] == "unittest":
        if course_config['variant'] == "pytest":
            return pytest_grader
        else:
            raise InvalidConfigError()
    else:
        raise InvalidConfigError()


def run_grader(course_name, lab):
    """
    All the possibly returned modules will have a run_grader function that will be invoked here
    """
    course_grader = select_course_grader(course_name)
    course_grader.run_grader(course_name, lab)

def run_grader_diff(course_name, lab):
    course_grader = select_course_grader(course_name)
    return course_grader.get_diff_results_file(course_name, lab)



def add_submissions(course_name, lab, submissions_file):
    """
    All the possibly returned modules will have a add_submissions function that will be invoked here
    """
    course_grader = select_course_grader(course_name)
    course_grader.add_submissions(course_name, lab, submissions_file)
    

def apply_moss(submissions_file, moss_parameters, course_name='cc451', lab='lab3'):
    """
    All the possibly returned modules will have a add_submissions function that will be invoked here
    """
    path_to_moss = Path(__file__).parent.joinpath('moss/submissions')
    submissions_extraction.extract_submissions(path_to_moss, submissions_file)
    moss_ = moss.Moss()
    moss_.set_config(moss_parameters, path_to_moss)
    response = moss_.get_result()
    return response




def save_single_submission(course_name, lab, file_in_memory, filename):
    course_grader = select_course_grader(course_name)
    course_grader.save_single_submission(
        course_name, lab, file_in_memory, filename)


def clear_submissions(course_name, lab):
    """
    Deletes everything inside the requested lab's submissions directory
    """
    course_grader = select_course_grader(course_name)
    course_grader.clear_submissions(course_name, lab)


def compressed_results(course_name, lab):
    """
    All the possibly returned modules will have a results_to_download function that will be invoked here
    """
    course_grader = select_course_grader(course_name)
    # returns a list of file paths
    results_files = course_grader.results_to_download(course_name, lab)
    # create a zip file of the returned file paths
    zip_file_path = helpers.create_zip_file(results_files)
    return zip_file_path

def get_diff_results_file(course_name, lab):
    path = Path("graderx").joinpath("graders").joinpath("courses").joinpath(course_name).joinpath(lab)
    file_path = path.joinpath(f"{lab}_diff_result.json")
    with open(file_path) as f:
     data = json.load(f)
     
    return data

def get_submission_files(course, lab, submission_id):
    course_grader = select_course_grader(course)
    submission_files_paths = course_grader.get_submission_files(course, lab, submission_id)
    if submission_files_paths:
        return list(map(lambda path: path.name, submission_files_paths))
    else:
        raise SubmissionNotFoundError

def update_submission_files(course, lab, submission_id, submission_files):
    course_grader = select_course_grader(course)
    try:
        course_grader.update_submission_files(course, lab, submission_id, submission_files)
    except FileNotFoundError:
        raise SubmissionNotFoundError

def get_submission_file_content(course, lab, submission_id, file_name):
    course_grader = select_course_grader(course)
    try:
        submission_file_content = course_grader.get_submission_file_content(course, lab, submission_id, file_name)
        return submission_file_content
    except FileNotFoundError:
        raise SubmissionFileNotFoundError

class InvalidConfigError(Exception):
    pass

class SubmissionNotFoundError(Exception):
    pass

class SubmissionFileNotFoundError(Exception):
    pass