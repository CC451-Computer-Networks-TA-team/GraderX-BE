import json
from .stdout_graders.c import c_grader
from .unittest_graders.pytest import pytest_grader
from pathlib import Path
from .lib import helpers
import os
from .moss import moss
from .stdout_graders.c.lib import submissions_extraction
from .stdout_graders.stdout_common import stdout_common
from .app_config import ( COURSES_DATA_PATH, MOSS_PATH, COURSE_NAME,
    COURSE_TYPE, COURSE_VARIANT, COURSE_LABS, LAB_NAME, 
    DISABLE_INTERNET, LAB_RUNTIME_LIMIT, LAB_TEST_CASES, PUBLIC_TEST_CASES )


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
    current_courses = get_courses()
    for course in current_courses:
        if course.lower() == course_name.lower():
            return "Course already present", 404
    current_courses = get_courses_config()
    stdout_common.create_course_dir(course_name)
    current_courses[course_name] = {
        COURSE_TYPE: "stdout", COURSE_VARIANT: language.lower(), COURSE_LABS: []}
    add_new_course_to_current_courses(current_courses)


def get_courses():
    return list(get_courses_config().keys())


def get_labs(course_name):
    return [lab[LAB_NAME] for lab in get_courses_config()[course_name][COURSE_LABS]]


def select_course_grader(course_name):
    """
    Finds the grader responsible for the given course then returns its main module
    """
    course_config = get_courses_config()[course_name]
    if course_config[COURSE_TYPE] == "stdout":
        if course_config[COURSE_VARIANT] == "c":
            return c_grader
        else:
            raise InvalidConfigError()
    elif course_config[COURSE_TYPE] == "unittest":
        if course_config[COURSE_VARIANT] == "pytest":
            return pytest_grader
        else:
            raise InvalidConfigError()
    else:
        raise InvalidConfigError()

def get_public_testcases(course, lab):
    courses_config = get_courses_config_if_course_exists(course)
    target_course = courses_config[course]
    target_lab_index = -1
    for i, lab_ in enumerate(target_course['labs']):
        if lab_['name'] == lab:
            target_lab_index = i
    if target_lab_index == -1:
        raise LabNotFoundError
    elif 'public_test_cases' not in target_course['labs'][target_lab_index]:
        return []
    else:
        return courses_config[course]['labs'][target_lab_index]['public_test_cases']

def run_grader(course_name, lab, student = False):
    """
    All the possibly returned modules will have a run_grader function that will be invoked here
    """
    course_grader = select_course_grader(course_name)
    if student:
        public_testcases = get_public_testcases(course_name, lab)
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
    all_courses = get_courses_config()
    if only_stdout:
        all_courses = {course_name: course_data for course_name,
                       course_data in all_courses.items() if course_data[COURSE_TYPE] == 'stdout'}
    for course_id, course_data in all_courses.items():
        course_data[COURSE_NAME] = course_id
    return list(all_courses.values())


def get_all_labs_data(course_id):
    course_labs = get_course_data(course_id)[COURSE_LABS]
    for index, lab in enumerate(course_labs):
        course_labs[index][LAB_TEST_CASES] = stdout_common.get_test_cases(
            course_id, lab[LAB_NAME])
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
    try:
        course_data = get_courses_config()[course_id]
    except KeyError:
        raise CourseNotFoundError()
    course_data[COURSE_NAME] = course_id
    return course_data


def get_course_data_with_test_cases(course_id):
    course_data = get_course_data(course_id)
    for index, lab in enumerate(course_data[COURSE_LABS]):
        course_data[COURSE_LABS][index][LAB_TEST_CASES] = stdout_common.get_test_cases(
            course_id, lab[LAB_NAME])
    return course_data


def update_course_data(course_id, new_course_data):
    courses_config = get_courses_config_if_course_exists(course_id)
    stdout_common.create_course_data(course_id, new_course_data[COURSE_LABS])
    for index, _ in enumerate(new_course_data[COURSE_LABS]):
        del new_course_data[COURSE_LABS][index][LAB_TEST_CASES]
    del new_course_data[COURSE_NAME]
    courses_config[course_id] = new_course_data
    update_course_config(courses_config)


def delete_course(course_id):
    courses_config = get_courses_config_if_course_exists(course_id)
    try:
        stdout_common.delete_course(course_id)
    except FileNotFoundError:
        pass
    del courses_config[course_id]
    update_course_config(courses_config)


def delete_lab(course_id, lab_id):
    courses_config = get_courses_config_if_course_exists(course_id)
    try:
        stdout_common.delete_lab(course_id, lab_id)
    except FileNotFoundError:
        pass
    courses_config[course_id][COURSE_LABS] = list(
        filter(lambda lab: lab[LAB_NAME] != lab_id, courses_config[course_id][COURSE_LABS]))
    update_course_config(courses_config)


def sanitize_and_validate_lab_data(lab_data):
    if LAB_NAME not in lab_data or len(lab_data[LAB_NAME]) > 20:
        raise InvalidLabDataError
    try:
        lab_data[LAB_RUNTIME_LIMIT] = int(lab_data[LAB_RUNTIME_LIMIT])
    except:
        raise InvalidLabDataError
    if DISABLE_INTERNET not in lab_data:
        raise InvalidLabDataError
    else:
        lab_data[DISABLE_INTERNET] = False if lab_data[DISABLE_INTERNET] == 'false' else True
    if lab_data[LAB_TEST_CASES]:
        lab_data[LAB_TEST_CASES] = json.loads(lab_data[LAB_TEST_CASES])

def add_lab(course_id, lab_data, lab_guide = None):
    courses_config = get_courses_config_if_course_exists(course_id)
    # Validate lab_data
    if LAB_NAME in lab_data and lab_data[LAB_NAME] in map(lambda lab: lab[LAB_NAME], courses_config[course_id][COURSE_LABS]):
        raise LabAlreadyExistsError
    sanitize_and_validate_lab_data(lab_data)
    # Start creating lab
    stdout_common.create_lab_dir(course_id, lab_data[LAB_NAME])
    if lab_data[LAB_TEST_CASES]:
        stdout_common.create_test_cases(course_id, lab_data[LAB_NAME], lab_data[LAB_TEST_CASES])
        lab_data[PUBLIC_TEST_CASES] = list(map(lambda tc: tc['id'], filter(lambda tc: tc['public'], lab_data[LAB_TEST_CASES])))
    del lab_data[LAB_TEST_CASES]
    if lab_guide:
        stdout_common.create_lab_guide(course_id, lab_data[LAB_NAME], lab_guide)
    else:
        # Using pop to avoid exception if 'lab_guide' is not in lab_data
        lab_data.pop('lab_guide', None)
    courses_config[course_id][COURSE_LABS].append(lab_data)
    update_course_config(courses_config)


def get_lab_guide_content(course, lab):
    course_grader = select_course_grader(course)
    try:
        lab_guide_content = course_grader.get_lab_guide_content(course, lab)
        return lab_guide_content
    except FileNotFoundError:
        raise LabHasNoGuideError


def edit_lab(course_id, lab_data):
    courses_config = get_courses_config_if_course_exists(course_id)
    # Validate lab_data
    if LAB_NAME in lab_data and lab_data[LAB_NAME] not in map(lambda lab: lab[LAB_NAME], courses_config[course_id][COURSE_LABS]):
        raise LabNotFoundError
    sanitize_and_validate_lab_data(lab_data)
    # Start creating lab
    stdout_common.clear_test_cases(course_id, lab_data[LAB_NAME])
    if lab_data[LAB_TEST_CASES]:
        stdout_common.create_test_cases(
            course_id, lab_data[LAB_NAME], lab_data[LAB_TEST_CASES])
    del lab_data[LAB_TEST_CASES]
    courses_config[course_id][COURSE_LABS] = list(filter(
        lambda lab: lab[LAB_NAME] != lab_data[LAB_NAME], courses_config[course_id][COURSE_LABS]))
    courses_config[course_id][COURSE_LABS].append(lab_data)
    update_course_config(courses_config)


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
