from werkzeug.datastructures import FileStorage
from pathlib import Path
import shlex
import subprocess
import os
## dependencies for docker
import patoolib
# pip install patool

def file_extract(file_path, verbosity=1):
    patoolib.extract_archive(file_path, verbosity=verbosity)
    os.remove(file_path)
    return True

def extract_submissions(dest_directory: Path, submissions_file: FileStorage,  verbosity= 0):
    """
    Args:
    dest_directory: Path. Submission directory found in [lab_name]/config.py
    submissions_file: FileStorage. It is used by the request object to represent uploaded files. 
 
    Returns: bool
    status: True on sucessful extraction

    Actions:
    extracts the submissions file in the destenation directory and removes the rar (or Whatever) file

    """
    EXTENSION = "rar"

    submissions_file.save(dst=dest_directory)
    file_name = submissions_file.filename

    # check if name contains an extension 
    if not file_name.endswith('.'+ EXTENSION):
       file_name += '.'+ EXTENSION

    file_path = dest_directory.joinpath(file_name)
    # check if exists
    status = [file_extract(file_path), True][os.path.exists(file_path)]
    return status



def run_grader_commands(course_code, lab_id):
    curr_dir = str(Path(__file__).parent.resolve())
    cmd = shlex.split(f"pytest -vv --tb=short --show-capture=no {curr_dir}/courses/{course_code}/app/{lab_id}/test_run_grader.py")
    file_name = "output.txt"
    with open(file_name, "w+") as f:
        subprocess.run(cmd, stdout=f)
    parser_file = "parser_output"
    lab_number = lab_id.split('lab')[-1]
    with open(file_name, "r") as fi:
        with open(parser_file, "w+") as fo:
            cmd = shlex.split(f"python {curr_dir}/courses/cc451/app/lib/console_log_parser.py {lab_number} {curr_dir}/courses/cc451/app/res/{lab_id}")
            subprocess.run(cmd, stdin=fi, stdout=fo)


def run_grader(course_code: str, lab_id: str, submissions_file: FileStorage) -> dict:
    curr_dir = str(Path(__file__).parent.resolve())
    try:
        extract_submissions(Path(f"{curr_dir}/courses/{course_code}/app/{lab_id}/submissions/2020"), submissions_file)
    except:
        return False
    run_grader_commands(course_code, lab_id)
    return True
    

def get_courses() -> list:
    """
    Returns a list of all the existing courses
    """
    p = Path(__file__).parent / 'courses'
    return [x.name for x in p.iterdir() if x.is_dir]


class EmptyCourseError(Exception):
    pass