from pathlib import Path
import json
from .lib import test_cases_parser as tc_parser


def add_test_case_file(path, tc_name, data):
    path = Path(path, tc_name)
    with path.open('w') as write_file:
        write_file.write(data)

def create_course_data(course_name, labs):
    labs_path = Path(__file__).joinpath(f"../../../courses/{course_name}/labs").resolve()
    for lab in labs:
        test_cases_path = labs_path.joinpath(f"{lab['name']}/test_cases")
        test_cases_path.mkdir(parents=True, exist_ok=True)
        create_test_cases(test_cases_path, lab['test_cases'])

def create_test_cases(path, test_cases):
    for tc in test_cases:
        add_test_case_file(path, f"{tc['id']}_in", tc['input'])
        add_test_case_file(path, f"{tc['id']}_out", tc['output'])

def get_lab_path(course, lab):
    return Path(__file__).joinpath(
        f'../../../courses/{course}/labs/{lab}').resolve()

def get_test_cases(course, lab):    
    test_cases_tuples = tc_parser.get_test_cases(get_lab_path(course, lab))
    return [{"id": tc[0],"input": tc[1], "output": tc[2]} for tc in test_cases_tuples]
