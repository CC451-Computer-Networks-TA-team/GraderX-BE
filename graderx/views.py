from pathlib import Path
from flask import request, jsonify, send_file
from graderx import app
from graderx.graders import manager
from werkzeug.utils import secure_filename
import os

available_labs = ['lab1_client', 'lab3']

ALLOWED_EXTENSIONS = {'rar'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/labs/cc451', methods=['GET'])
def get_labs():
    """
    Returns the lab names of the available labs
    """
    # TODO: make the cc451 grader comply with the directory structure to support dynamic lab names fetch
    return jsonify({
        'labs': available_labs
    }), 200


@app.route('/courses', methods=['GET'])
def get_courses():
    """
    Returns all the existing courses
    """
    courses = manager.get_courses()
    return jsonify({
        'courses': courses
    }), 200


@app.route('/results/<course_code>/<lab_id>', methods=["POST"])
def generate_results(course_code, lab_id):
    """
    Recieves the submissions of the lab identified by course_code and lab_id
    then runs the grader through manager then informs the client with the status
    """
    # ensure that the submissions file is in the request
    if 'submissions_file' not in request.files:
        return jsonify({'status': 'submissions file must be included'}), 400
    submissions_file = request.files['submissions_file']
    if submissions_file.filename == '':
        return jsonify({
            'status': "no selected file"
        }), 400
    if submissions_file and allowed_file(submissions_file.filename):
        #TODO: secure filename
        if lab_id in available_labs:
            status = manager.run_grader(course_code, lab_id, submissions_file)
            return jsonify({
                'status': "SUCCESS" if status else "FAIL"
            }), 200
        else:
            return jsonify({
                'status': f"no lab with the id {lab_id} does not exist"
            }), 404

@app.route('/results/<course_code>/<lab_id>', methods=["GET"])
def get_results(course_code, lab_id):
    path_to_result = Path(__file__).parent / 'graders/courses/cc451/app/res/' / lab_id
    if path_to_result.exists():
        return send_file(str(path_to_result))
    else:
        return "Results file for this lab not found, you must upload submissions first", 404
    
