from graderx import app
from graderx.graders import manager
from flask import request, jsonify, send_file
from enum import Enum
from graderx.graders import import_submissions


ALLOWED_EXTENSIONS = {'rar', '7z', 'zip'}


def allowed_file(filename):
    """
    Check if the filename's extension is one of the allowed extensions
    >>> allowed_file("my-file.pdf")
    False
    >>> allowed_file("my-file.zip")
    True
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class UPLOAD_STATUS(Enum):
    """
    Status messages sent to the client
    """
    FILE_NOT_INCLUDED = 'submissions file must be included'
    FILE_NOT_SELECTED = "no selected file"
    FILE_EMPTY = "the uploaded file is empty"
    UNSUPPORTED_FILE = "the file type is not supported, supported types are " + \
        ', '.join(ALLOWED_EXTENSIONS)
    GRADER_FAILED = "FAIL"
    SUCCESS = "SUCCESS"


@app.route('/courses')
def get_courses():
    return jsonify({"courses": manager.get_courses()})


@app.route('/courses/<course_name>/labs')
def get_labs(course_name):
    """
    Responds with with a list of labs for the specified course
    Example:GET /courses/cc451/labs
    Response body: {"labs": ["lab1_client", "lab1_server", "lab3", "lab4"]}
    """
    return jsonify({"labs": manager.get_labs(course_name)})


@app.route('/run_grader')
def start_grading():
    """
    Takes 2 query parameters "course" and "lab", then calls the run_grader of the manager
    which determine the corresponding grader to run
    Example:GET /run_grader?course=cc451&lab=lab3
    """
    try:
        course_name = request.args['course']
        lab_name = request.args['lab']
    except KeyError:
        return jsonify({'status': "course and lab query parameters must be included"}), 400
    try:
        manager.run_grader(course_name, lab_name)
        return "SUCCESS", 200
    except:
        return "Failed to run the grader", 500


@app.route('/submissions', methods=['POST'])
def add_submissions():
    """
    Takes 3 query paramteres "course", "lab" and "method"
    "method" determines how these submissions are added
    > example:POST /submissions?course=cc451&lab=lab3&method=file
    given that a "file" method is specified, a file must be sent with the request
    which should be a compressed file with the submissions which will be extracted
    > another example would be: POST /submissions?course=cc451&lab=lab3&method=import-google
    in this case import-google method is specified so the request body should have access_token
    and sheet_link to be imported from
    """
    try:
        course_name = request.args['course']
        lab_name = request.args['lab']
        method = request.args['method']
    except KeyError:
        return jsonify({'status': "course, lab and method query parameters must be included"}), 400
    if method == "file":
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
                manager.add_submissions(
                    course_name, lab_name, submissions_file)
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
    elif method =="file-moss":
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
                res = manager.apply_moss(
                    submissions_file, request.form)
                return jsonify(res), 200
            except:
                return jsonify({
                    'status': UPLOAD_STATUS.GRADER_FAILED.value
                }), 500
        else:
            return jsonify({
                'status': UPLOAD_STATUS.UNSUPPORTED_FILE.value
            }), 400
    elif method == "import-google":
        access_token = request.json['accessToken']
        sheet_link = request.json['sheetLink']
        # Checks if the field parameter is included and not empty
        if 'field' in request.args and request.args.get('field'):
            importer = import_submissions.GoogleImportSubmissions(
                access_token, sheet_link, course_name, lab_name, request.args.get('field'))
        else:
            importer = import_submissions.MSImportSubmissions(
                access_token, sheet_link, course_name, lab_name)
        try:
            importer.import_submissions()
            return "SUCCESS", 200
        except:
            # TODO: handle detectable exceptions
            return "Failed to import submissions", 500

    elif method == "import-ms":
        access_token = request.json['accessToken']
        sheet_link = request.json['sheetLink']     
        importer = import_submissions.MSImportSubmissions(
                access_token, sheet_link, course_name, lab_name)
        try:
            importer.import_submissions()
            return "SUCCESS", 200
        except:
            # TODO: handle detectable exceptions
            return "Failed to import submissions", 500


@app.route('/results')
def get_results():
    """
    Takes 3 query parameters "course", "lab" and "type"
    "type" determines the form of the results in the response
    > for example: GET /results?course=cc451&lab=lab3&type=download
    will send the results in a compressed file attached to the response
    > GET /results?course=cc451&lab=lab3&type=json
    will send the results in the response body as a json object so that it can be easily parsed and used
    in the client side
    """
    try:
        course_name = request.args['course']
        lab_name = request.args['lab']
        results_type = request.args['type']
    except KeyError:
        return jsonify({'status': "course, lab and type query parameters must be included"}), 400

    if results_type == "download":
        try:
            return send_file(manager.compressed_results(course_name, lab_name))
        except:
            return jsonify({
                'status': "Failed to fetch results, please make sure you run the grader first"
            }), 400

    elif results_type == "diff":
        # change it to (test_course)
        if course_name == "test_course":
            #return jsonify(manager.run_grader_diff(course_name, lab_name)), 200
            try:
                return jsonify(manager.run_grader_diff(course_name, lab_name)), 200
                # return jsonify(manager.get_diff_results_file(course_name, lab_name)), 200
            except:
                return jsonify({
                    'status': "Failed to fetch diff results, please make sure you run the grader first"
                }), 400
    else:
        return jsonify({
            'status': "Failed to fetch results, please make sure you run the grader first"
        }), 500


@app.route('/submissions/validate', methods=['POST'])
def validate_import_source():
    """
    Verifies that the sheet link is valid and accessible
    """
    access_token = request.json['accessToken']
    sheet_link = request.json['sheetLink']
    method = request.json['method']
    

    if method == 'import-google':

        try:
            importer = import_submissions.GoogleImportSubmissions(
                access_token, sheet_link)
        except:
            # TODO: handle detectable exceptions
            return "Invalid sheet link", 400
        try:
            importer.only_one_uploads_column()
            return "SUCCESS", 200
        except import_submissions.TooManyUploadColumnsError as e:
            fields = importer.get_url_fields()
            return jsonify({'msg': str(e), 'fields': fields}), 400
        except import_submissions.InvalidSheetError as e:
            return str(e), 400
        except:
            return "An unexpected error occured", 500
    elif method == 'import-ms':
        try:
            importer = import_submissions.MSImportSubmissions(
                access_token, sheet_link)
            return "SUCCESS", 200

        except:
            # TODO: handle detectable exceptions
            return "Invalid sheet link", 400

