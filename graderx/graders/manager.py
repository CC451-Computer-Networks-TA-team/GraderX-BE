from werkzeug.datastructures import FileStorage
from pathlib import Path
import shlex
import subprocess


def get_results(course_code: str, lab_id: str) -> dict:
    curr_dir = str(Path(__file__).parent.resolve())
    print(curr_dir)
    cmd = shlex.split(f"pytest -vv --tb=short --show-capture=no {curr_dir}/courses/{course_code}/app/{lab_id}/test_run_grader.py")
    file_name = "output.txt"
    with open(file_name, "w+") as f:
        subprocess.run(cmd, stdout=f)
    parser_file = "parser_output"
    with open(file_name, "r") as fi:
        with open(parser_file, "w+") as fo:
            cmd = shlex.split(f"python {curr_dir}/courses/cc451/app/lib/console_log_parser.py 1_client")
            subprocess.run(cmd, stdin=fi, stdout=fo)
    # TODO-TICKET-139:should return the results file
    return "GRADED"
    

def get_courses() -> list:
    """
    Returns a list of all the existing courses
    """
    p = Path(__file__).parent / 'courses'
    return [x.name for x in p.iterdir() if x.is_dir]


class EmptyCourseError(Exception):
    pass