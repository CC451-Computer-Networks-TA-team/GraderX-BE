import sys
from pathlib import Path
# Adding courses_metadata_manager directory to path to be able to unpickle from manager
# https://stackoverflow.com/a/45264751
sys.path.append(str(Path(__file__).parent.joinpath('courses_metadata').resolve()))
import json
from .stdout_graders.c import c_grader
from .unittest_graders.pytest import pytest_grader
from .lib import helpers
import os
from .moss import moss
from .stdout_graders.c.lib import submissions_extraction
from .stdout_graders.stdout_common import stdout_common
from .app_config import ( COURSES_DATA_PATH, MOSS_PATH, COURSE_NAME,
    COURSE_TYPE, COURSE_VARIANT, COURSE_LABS, LAB_NAME, 
    DISABLE_INTERNET, LAB_RUNTIME_LIMIT, LAB_TEST_CASES, PUBLIC_TEST_CASES )
from .courses_metadata.courses_metadata_manager import (Course, Lab, load_courses_data ,get_courses_names, 
    get_course_by_name)


def get_courses_config():
    """
    Creates a dict out of courses_config json file then returns it
    """
    with open(COURSES_DATA_PATH) as f:
        return json.load(f)


def get_courses_config_if_course_exists(course_name):
    courses_config = get_courses_config()
    if course_name not in courses_config:
        raise CourseNotFoundError
    return courses_config


def update_course_config(course_config_dict):
    """
    Takes a dict and replaces the current courses_config with it
    """
    with open(COURSES_DATA_PATH, "w") as f:
        json.dump(course_config_dict, f)


def add_new_course_to_current_courses(data):
    with open(COURSES_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_course(course_name, language, labs):
    new_course = Course(course_name, language)
    new_course.save()
    stdout_common.create_course_dir(course_name)


def select_course_grader(course_name):
    """
    Finds the grader responsible for the given course then returns its main module
    """
    course = get_course_by_name(course_name)
    if course.type_ == "stdout":
        if course.variant == "c":
            return c_grader
        else:
            raise InvalidConfigError()
    elif course.type_ == "unittest":
        if course.variant == "pytest":
            return pytest_grader
        else:
            raise InvalidConfigError()
    else:
        raise InvalidConfigError()


def run_grader(course_name, lab, student = False):
    """
    All the possibly returned modules will have a run_grader function that will be invoked here
    """
    course_grader = select_course_grader(course_name)
    if student:
        public_testcases = get_course_by_name(course_name).get_lab_by_name(lab).public_test_cases
        if public_testcases:
            course_grader.run_grader(course_name, lab, public_testcases)
        else:
            raise NoPublicTestcasesError
    else:
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
    submissions_extraction.extract_submissions(MOSS_PATH, submissions_file)
    moss_ = moss.Moss()
    moss_.set_config(moss_parameters, MOSS_PATH)
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
    path = Path("graderx").joinpath("graders").joinpath(
        "courses").joinpath(course_name).joinpath(lab)
    file_path = path.joinpath(f"{lab}_diff_result.json")
    with open(file_path) as f:
        data = json.load(f)
    return data


def get_all_courses_data(only_stdout=False):
    all_courses = load_courses_data()
    if only_stdout:
        return [course.dict_repr() for course in all_courses if course.type_ == 'stdout']
    else:
        return [course.dict_repr() for course in all_courses]


def get_all_labs_data(course_id):
    course_labs = [lab.dict_repr() for lab in get_course_by_name(course_id).labs]
    for lab in course_labs:
        lab['test_cases'] = stdout_common.get_test_cases(
            course_id, lab['name'])
    return course_labs


def get_submission_files(course, lab, submission_id):
    course_grader = select_course_grader(course)
    submission_files_paths = course_grader.get_submission_files(
        course, lab, submission_id)
    if submission_files_paths:
        return list(map(lambda path: path.name, submission_files_paths))
    else:
        raise SubmissionNotFoundError


def update_submission_files(course, lab, submission_id, submission_files):
    course_grader = select_course_grader(course)
    try:
        course_grader.update_submission_files(
            course, lab, submission_id, submission_files)
    except FileNotFoundError:
        raise SubmissionNotFoundError


def get_submission_file_content(course, lab, submission_id, file_name):
    course_grader = select_course_grader(course)
    try:
        submission_file_content = course_grader.get_submission_file_content(
            course, lab, submission_id, file_name)
        return submission_file_content
    except FileNotFoundError:
        raise SubmissionFileNotFoundError


def get_submissions_list(course, lab):
    course_grader = select_course_grader(course)
    submissions_list = course_grader.get_not_fullmark_submissions(course, lab)
    return submissions_list


def get_course_data(course_id):
    return get_course_by_name(course_id).dict_repr()


def get_course_data_with_test_cases(course_id):
    course_data = get_course_by_name(course_id).dict_repr()
    for lab in course_data.labs:
        lab['test_cases'] = stdout_common.get_test_cases(
            course_id, lab['name'])
    return course_data


def update_course_data(course_id, new_course_data):
    course = get_course_by_name(course_id)
    course.variant = new_course_data['variant']
    course.update()


def delete_course(course_id):
    course = get_course_by_name(course_id)
    course.delete()
    try:
        stdout_common.delete_course(course_id)
    except FileNotFoundError:
        pass


def delete_lab(course_id, lab_id):
    course = get_course_by_name(course_id)
    course.delete_lab(lab_id)
    course.update()
    try:
        stdout_common.delete_lab(course_id, lab_id)
    except FileNotFoundError:
        pass


def add_lab(course_id, lab_data, lab_guide = None):
    course = get_course_by_name(course_id)
    new_lab = Lab(lab_data[LAB_NAME], lab_data[DISABLE_INTERNET], lab_data[LAB_RUNTIME_LIMIT])
    test_cases = json.loads(lab_data[LAB_TEST_CASES]) if lab_data[LAB_TEST_CASES] else [] 
    # Start creating lab
    stdout_common.create_lab_dir(course_id, new_lab.name)
    if test_cases:
        stdout_common.create_test_cases(course_id, new_lab.name, test_cases)
        new_lab.public_test_cases = list(map(lambda tc: tc['id'], filter(lambda tc: tc['public'], test_cases)))
    if lab_guide:
        stdout_common.create_lab_guide(course_id, new_lab.name, lab_guide)
    course.add_lab(new_lab)
    course.update()

def get_lab_guide_content(course, lab):
    course_grader = select_course_grader(course)
    try:
        lab_guide_content = course_grader.get_lab_guide_content(course, lab)
        return lab_guide_content
    except FileNotFoundError:
        raise LabHasNoGuideError


def edit_lab(course_id, lab_data):
    course = get_course_by_name(course_id)
    lab = course.get_lab_by_name(lab_data[LAB_NAME])
    test_cases = json.loads(lab_data[LAB_TEST_CASES]) if lab_data[LAB_TEST_CASES] else [] 
    # Start creating lab
    stdout_common.clear_test_cases(course_id, lab.name)
    if test_cases:
        stdout_common.create_test_cases(
            course_id, lab.name, test_cases)
        lab.public_test_cases = list(map(lambda tc: tc['id'], filter(lambda tc: tc['public'], test_cases)))
    lab.disable_internet = lab_data[DISABLE_INTERNET]
    lab.runtime_limit = lab_data[LAB_RUNTIME_LIMIT]
    course.update()

class InvalidConfigError(Exception):
    pass


class SubmissionNotFoundError(Exception):
    pass


class SubmissionFileNotFoundError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class LabNotFoundError(Exception):
    pass

class LabHasNoGuideError(Exception):
    pass

class NoPublicTestcasesError(Exception):
    pass


class LabAlreadyExistsError(Exception):
    pass


class InvalidLabDataError(Exception):
    pass
