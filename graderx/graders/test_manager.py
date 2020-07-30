from . import manager
import pytest
from pathlib import Path
import shutil, random, string


def generate_random_code():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                          for _ in range(12))

def test_exception_if_course_empty():
    course_code = generate_random_code()
    p = Path(__file__).parent / 'courses' / course_code / 'labs'
    p.mkdir(parents=True, exist_ok=True)
    with pytest.raises(manager.EmptyCourseError):
        assert manager.get_lab_ids(course_code)
    p.rmdir()
    p.parent.rmdir()


def test_exception_if_course_not_exist():
    course_code = generate_random_code()
    with pytest.raises(FileNotFoundError):
        assert manager.get_lab_ids(course_code)


def test_receives_course_labs():
    course_code = generate_random_code()
    p = Path(__file__).parent / 'courses' / course_code / 'labs'
    labs_paths = [p / 'lab1', p / 'lab300']
    labs_paths[0].mkdir(parents=True)
    labs_paths[1].mkdir(parents=True)
    # map(lambda x: x.mkdir(parents=True), labs_paths)
    assert set(manager.get_lab_ids(course_code)) == {'lab1', 'lab300'}
    shutil.rmtree(str(Path(__file__).parent / 'courses' / course_code))


def test_receives_correct_courses_list():
    course_code = generate_random_code()
    p = Path(__file__).parent / 'courses' / course_code
    p.mkdir(parents=True)
    assert course_code in manager.get_courses()
    p.rmdir()
