from pathlib import Path
from flask import request, jsonify, send_file
from graderx import app
from graderx.graders import manager
from werkzeug.utils import secure_filename
import os
from enum import Enum
from functools import partial

AVAILABLE_LABS = ['lab1_client', 'lab3']

ALLOWED_EXTENSIONS = {'rar', '7z', 'zip'}


def lab_not_exist_status(lab_id):
    return f'{lab_id} does not exist'


class UPLOAD_STATUS(Enum):
    LAB_NOT_EXIST = partial(lab_not_exist_status)
    FILE_NOT_INCLUDED = 'submissions file must be included'
    FILE_NOT_SELECTED = "no selected file"
    FILE_EMPTY = "the uploaded file is empty"
    UNSUPPORTED_FILE = "the file type is not supported, supported types are " + \
        ', '.join(ALLOWED_EXTENSIONS)
    GRADER_FAILED = "FAIL"
    SUCCESS = "SUCCESS"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/labs/cc451', methods=['GET'])
def get_labs():
    """
    Returns the lab names of the available labs
    """
    return jsonify({
        'labs': AVAILABLE_LABS
    }), 200


@app.route('/results/cc451/<lab_id>', methods=["POST"])
def generate_results(lab_id):
    """
    Recieves the submissions of the lab identified by lab_id
    then runs the grader through manager then informs the client with the status
    """
    if lab_id not in AVAILABLE_LABS:
        return jsonify({'status': UPLOAD_STATUS.LAB_NOT_EXIST.value(lab_id)}), 404

    # ensure that the submissions file is in the request
    if 'submissions_file' not in request.files:
        return jsonify({'status': UPLOAD_STATUS.FILE_NOT_INCLUDED.value}), 400

    submissions_file = request.files['submissions_file']
    if submissions_file.filename == '':
        return jsonify({
            'status': UPLOAD_STATUS.FILE_NOT_SELECTED.value
        }), 400

    # submissions_file will be falsy if the file is empty
    if not submissions_file:
        return jsonify({
            'status': UPLOAD_STATUS.FILE_EMPTY.value
        }), 400

    if allowed_file(submissions_file.filename):
        # TODO: secure filename
        try:
            manager.run_grader(lab_id, submissions_file)
            return jsonify({
                'status': UPLOAD_STATUS.SUCCESS.value
            }), 200
        except:
            return jsonify({
                'status': UPLOAD_STATUS.GRADER_FAILED.value
            }), 500
    else:
        return jsonify({
            'status': UPLOAD_STATUS.UNSUPPORTED_FILE.value
        }), 400


@app.route('/results/cc451/<lab_id>', methods=["GET"])
def get_results(lab_id):
    # TODO: secure filename
    path_to_result = Path(__file__).parent / \
        'graders/courses/cc451/app/res/' / lab_id
    if path_to_result.exists():
        return send_file(str(path_to_result))
    else:
        return "Results file for this lab not found, you must upload submissions first", 404
