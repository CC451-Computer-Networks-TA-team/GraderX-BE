import json
from .stdout_graders.c import c_grader
from .unittest_graders.pytest import pytest_grader
from pathlib import Path
from .lib import helpers
import os
from .moss import moss
from .stdout_graders.c.lib import submissions_extraction
from .stdout_graders.stdout_common import stdout_common
    

def get_courses_config():
    """
    Creates a dict out of courses_config json file then returns it
    """
    with open(Path(__file__).parent.joinpath("courses_config.json")) as f:
        return json.load(f)

def update_course_config(course_config_dict):
    """
    Takes a dict and replaces the current courses_config with it
    """
    with open(Path(__file__).parent.joinpath("courses_config.json"), "w") as f:
        json.dump(course_config_dict, f)


def add_new_course_to_current_courses(data):
    with open(Path(__file__).parent.joinpath("courses_config.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_course(course_name, language, labs):
    current_courses = get_courses() 
    for course in current_courses:
        if course.lower() == course_name.lower():
            return "Course already present", 404
    current_courses = get_courses_config()
    stdout_common.create_course_data(course_name, labs)
    for index, lab in enumerate(labs):
        del labs[index]['test_cases']
    current_courses[course_name] = {"type": "stdout", "variant": language, "labs": labs}
    add_new_course_to_current_courses(current_courses)


def get_courses():
    return list(get_courses_config().keys())


def get_labs(course_name):
    return [lab["name"] for lab in get_courses_config()[course_name]['labs']]


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


def get_all_courses_data():
    all_courses = get_courses_config()
    for course_id, course_data in all_courses.items():
        course_data['name'] = course_id
    return list(all_courses.values())

def get_all_labs_data(course_id):
    course_labs = get_course_data(course_id)['labs']
    return course_labs

def get_course_data(course_id):
    try:
        course_data = get_courses_config()[course_id]
    except KeyError:
        raise CourseNotFoundError()
    course_data['name'] = course_id
    return course_data


def get_course_data_with_test_cases(course_id):
    course_data = get_course_data(course_id)
    for index, lab in enumerate(course_data['labs']):
        course_data['labs'][index]["test_cases"] = stdout_common.get_test_cases(course_id, lab["name"])
    return course_data

def update_course_data(course_id, new_course_data):
    courses_config = get_courses_config()
    if course_id not in courses_config:
        raise CourseNotFoundError
    stdout_common.create_course_data(course_id, new_course_data['labs'])
    for index, _ in enumerate(new_course_data['labs']):
        del new_course_data['labs'][index]['test_cases']
    del new_course_data['name']
    courses_config[course_id] = new_course_data
    update_course_config(courses_config)

def delete_course(course_id):
    courses_config = get_courses_config()
    if course_id not in courses_config:
        raise CourseNotFoundError
    stdout_common.delete_course(course_id)
    del courses_config[course_id]
    update_course_config(courses_config)


class InvalidConfigError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass

class SubmissionNotFoundError(Exception):
    pass