from flask import request, jsonify
from graderx import app
from graderx.graders import manager

available_labs = ['lab1_client', 'lab3']

@app.route('/labs/cc451', methods=['GET'])
def get_labs():
    """
    Returns the lab names of the available labs
    """
    #TODO: make the cc451 grader comply with the directory structure to support dynamic lab names fetch
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


@app.route('/results/<course_code>/<lab_id>', methods=["GET"])
def generate_results(course_code, lab_id):
    """
    Recieves the submissions of the lab identified by course_code and lab_id
    gets the grades from the graders manager then send it back to the frontend
    """
    # TODO: receive the uploaded file when TICKET-148 is completed
    if lab_id in available_labs:
        status = manager.get_results(course_code, lab_id)
        return jsonify({
            'status': status
        }), 200
    else:
        return jsonify({
            'status': f"lab {lab_id} does not exist"
        }), 404