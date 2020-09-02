from graderx import app
import pytest
from graderx.graders import manager
from graderx import views
import shutil
import random
import string
from pathlib import Path
import flask
from io import BytesIO


def generate_random_code():
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(12))


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client




def test_receives_available_labs(client):
    """
    Test if the client receives the currently available labs
    """
    rv = client.get('/labs/cc451')
    assert rv.json['labs'] == views.AVAILABLE_LABS


def test_receives_correct_lab_results(client):
    lab_id = generate_random_code()
    path_to_result = Path(__file__).parent / \
        f'graders/courses/cc451/app/res/{lab_id}'
    path_to_result.parent.mkdir(exist_ok=True)
    with path_to_result.open("w") as f:
        f.write("Hello, World")
    rv = client.get(f'/results/cc451/{lab_id}')
    assert rv.get_data(as_text=True) == "Hello, World"
    path_to_result.unlink()


def test_receives_proper_status_if_results_not_found(client):
    lab_id = generate_random_code()
    rv = client.get(f"/results/cc451/{lab_id}")
    assert rv.status_code == 404

def test_status_unavailable_lab_provided(client):
    lab_id = generate_random_code()
    rv = client.post(f"/results/cc451/{lab_id}")
    assert rv.json['status'] == views.UPLOAD_STATUS.LAB_NOT_EXIST.value(lab_id) and rv.status_code == 404


def test_status_no_file_key_is_sent(client):
    lab_id = views.AVAILABLE_LABS[0]
    rv = client.post(f"/results/cc451/{lab_id}")
    assert rv.json['status'] == views.UPLOAD_STATUS.FILE_NOT_INCLUDED.value and rv.status_code == 400


def test_status_no_file_included(client):
    lab_id = views.AVAILABLE_LABS[0]
    rv = client.post(f"/results/cc451/{lab_id}", buffered=True,
                           content_type='multipart/form-data',
                           data={'submissions_file' : (BytesIO(), '')})
    assert rv.json['status'] == views.UPLOAD_STATUS.FILE_NOT_SELECTED.value and rv.status_code == 400


def test_status_file_unsupported(client):
    lab_id = views.AVAILABLE_LABS[0]
    rv = client.post(f"/results/cc451/{lab_id}", buffered=True,
                           content_type='multipart/form-data',
                           data={'submissions_file' : (BytesIO(b'hello, world'), 'file.txt')})
    assert rv.json['status'] == views.UPLOAD_STATUS.UNSUPPORTED_FILE.value and rv.status_code == 400

def test_status_failed_grading(monkeypatch, client):
    def mock_run_grader(lab_id, submissions_file):
        raise Exception
    
    monkeypatch.setattr(manager, "run_grader",mock_run_grader)
    lab_id = views.AVAILABLE_LABS[0]
    rv = client.post(f"/results/cc451/{lab_id}", buffered=True,
                           content_type='multipart/form-data',
                           data={'submissions_file' : (BytesIO(b'my file contents'), 'myfile.rar')})
    assert rv.json['status'] == views.UPLOAD_STATUS.GRADER_FAILED.value


def test_status_successful_grading(monkeypatch, client):
    def mock_run_grader(lab_id, submissions_file):
        return True
    
    monkeypatch.setattr(manager, "run_grader",mock_run_grader)
    lab_id = views.AVAILABLE_LABS[0]
    rv = client.post(f"/results/cc451/{lab_id}", buffered=True,
                           content_type='multipart/form-data',
                           data={'submissions_file' : (BytesIO(b'my file contents'), 'myfile.rar')})
    assert rv.json['status'] == views.UPLOAD_STATUS.SUCCESS.value

