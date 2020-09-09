from pathlib import Path
import json


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
        pre_tc = path
        for tc in lab['test_cases']:
            path = Path(path, f"{tc['tc_id']}_in")
            path.touch()
            with path.open('w') as wf:
                wf.write(tc['input'])
            path = pre_tc
            path = Path(path, f"{tc['tc_id']}_out")
            path.touch()
            with path.open('w') as wf:
                wf.write(tc['output'])
            path = pre_tc
        path = dir_path

