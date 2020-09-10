from pathlib import Path
import json

def add_test_case_file(path, tc_name, data):
    path = Path(path, tc_name)
    path.touch()
    with path.open('w') as write_file:
        write_file.write(data)

def create_course_data(course_name, labs):
    path = Path(__file__).parent.parent.parent.joinpath("courses") / course_name
    path.mkdir()
    path = path / "labs"
    path.mkdir()
    dir_path = path
    for lab in labs:
        path = path / lab['name']
        path.mkdir()
        path = path / 'test_cases'
        path.mkdir()
        for tc in lab['test_cases']:
            add_test_case_file(path, f"{tc['tc_id']}_in", tc['input'])
            add_test_case_file(path, f"{tc['tc_id']}_out", tc['output'])
        path = dir_path

