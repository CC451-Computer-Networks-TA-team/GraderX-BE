from flask import request, jsonify
from graderx import app
from graderx.graders import manager


@app.route('/labs/<course_code>', methods=['GET'])
def get_labs(course_code):
    """
    Returns the lab names of a given course
    """
    try:
        labs = manager.get_lab_ids(course_code)
    except manager.EmptyCourseError as e:
        return jsonify({
            'msg': str(e)
        }), 400
    except FileNotFoundError:
        return jsonify({
            'msg': "The requested course does not exist"
        }), 404
    return jsonify({
        'labs': labs
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
