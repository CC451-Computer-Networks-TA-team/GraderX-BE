from pathlib import Path
import json
from .lib import test_cases_parser as tc_parser
import shutil


def add_test_case_file(path, tc_name, data):
    path = Path(path, tc_name)
    with path.open('w') as write_file:
        write_file.write(data)

def create_course_dir(course_name):
    course_path = Path(__file__).joinpath(f"../../../courses/{course_name}").resolve()
    course_path.mkdir(parents=True, exist_ok=True)

def create_lab_dir(course, lab):
    lab_path = Path(__file__).joinpath(f"../../../courses/{course}/labs/{lab}").resolve()
    lab_path.mkdir(parents=True, exist_ok=True)


def create_course_data(course_name, labs):
    labs_path = Path(__file__).joinpath(f"../../../courses/{course_name}/labs").resolve()
    for lab in labs:
        test_cases_path = labs_path.joinpath(f"{lab['name']}/test_cases")
        test_cases_path.mkdir(parents=True, exist_ok=True)

def create_test_cases(course, lab, test_cases):
    test_cases_path = Path(__file__).joinpath(f"../../../courses/{course}/labs/{lab}/test_cases").resolve()
    test_cases_path.mkdir(parents=True, exist_ok=True)
    for tc in test_cases:
        add_test_case_file(test_cases_path, f"{tc['id']}_in", tc['input'])
        add_test_case_file(test_cases_path, f"{tc['id']}_out", tc['output'])

def clear_test_cases(course, lab):
    test_cases_path = Path(__file__).joinpath(f"../../../courses/{course}/labs/{lab}/test_cases").resolve()
    if test_cases_path.exists():
        shutil.rmtree(str(test_cases_path))

def get_lab_path(course, lab):
    return Path(__file__).joinpath(
        f'../../../courses/{course}/labs/{lab}').resolve()

def get_course_path(course):
    return Path(__file__).joinpath(
        f'../../../courses/{course}').resolve()

def get_test_cases(course, lab):
    lab_path = get_lab_path(course, lab)
    if not lab_path.joinpath('test_cases').exists():
        return []
    test_cases_tuples = tc_parser.get_test_cases(lab_path)
    return [{"id": tc[0],"input": tc[1], "output": tc[2]} for tc in test_cases_tuples]

def delete_course(course_name):
    shutil.rmtree(str(get_course_path(course_name)))

def delete_lab(course, lab):
    shutil.rmtree(str(get_lab_path(course, lab)))