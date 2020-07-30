from graderx import app
import pytest
from graderx.graders import manager


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_receives_courses_list(monkeypatch, client):
    """
    Test if the client receives a list of the available courses when requesting /courses GET
    """
    def mock_get_courses():
        return ["course1", "course2", "course3"]
    monkeypatch.setattr(manager, "get_courses", mock_get_courses)
    rv = client.get('/courses')
    assert rv.json['courses'] == ["course1", "course2", "course3"]


def test_receives_labs_of_course(monkeypatch, client):
    """
    Test if the client receives the available to labs of a chosen course
    assuming that course exists and it has labs
    """
    def mock_get_lab_ids(course_id):
        return ['lab1', 'lab2', 'lab3']

    monkeypatch.setattr(manager, "get_lab_ids", mock_get_lab_ids)
    rv = client.get('/labs/cc451')
    assert rv.json['labs'] == ['lab1', 'lab2', 'lab3']


def test_receives_400_if_empty_course(monkeypatch, client):
    """
    Test if the client receives a 400 response with the expected message 
    """
    class EmptyCourseError(Exception):
        pass

    def mock_get_lab_ids(course_id):
        raise EmptyCourseError("The requested course has no labs")

    monkeypatch.setattr(manager, "get_lab_ids", mock_get_lab_ids)
    monkeypatch.setattr(manager, "EmptyCourseError", EmptyCourseError)
    rv = client.get('/labs/cc456')
    assert rv.status_code == 400 and rv.json['msg'] == "The requested course has no labs"


def test_receives_404_if_course_not_exist(monkeypatch, client):
    def mock_get_lab_ids(course_id):
        raise FileNotFoundError

    monkeypatch.setattr(manager, "get_lab_ids", mock_get_lab_ids)
    rv = client.get('/labs/cc999')
    assert rv.status_code == 404 and rv.json['msg'] == "The requested course does not exist"
