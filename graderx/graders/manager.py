from werkzeug.datastructures import FileStorage
from pathlib import Path


def get_lab_ids(course_code: str) -> list:
    """
    Returns a list of lab names of the given course
    """
    # gets the path of the parent of the current file 
    # and appends '/courses/{course_code}/labs' to it
    p = Path(__file__).parent / 'courses' / course_code / 'labs'
    ids = [x.name for x in p.iterdir() if x.is_dir()]
    if not ids:
        raise EmptyCourseError("The requested course has no labs")
    return ids


def get_courses() -> list:
    """
    Returns a list of all the existing courses
    """
    p = Path(__file__).parent / 'courses'
    return [x.name for x in p.iterdir() if x.is_dir]


class EmptyCourseError(Exception):
    pass
