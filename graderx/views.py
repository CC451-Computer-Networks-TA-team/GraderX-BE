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

@app.route('/course', methods=['POST'])
def create_course():
    """
    Takes a json object that has the needed data: 
        1- courseName: new course name
        2- langugae: Programming language to be used with this course labs
        3- labs: An array that has the test cases to be runned, time limit for each test case
        4- course type: type of grader to be used with this course (unit testing / stdout cases comparison)
    """
    try:
        courseName = request.json['name']
        language = request.json['variant']
        labs = request.json['labs']
    except KeyError:
        return jsonify({"message": "course name, language, and labs parameters must be included"}), 400
    try:
        manager.create_course(courseName, language, labs)
        return jsonify({"message": "SUCCESS"}), 200
    except:
        return jsonify({"message": "An error occured"}), 500


@app.route('/courses/<course_name>', methods=['DELETE'])
def delete_course(course_name):
    try:
        manager.delete_course(course_name)
        return jsonify({"message": "SUCCESS"}), 200
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404
    except:
        return jsonify({"message": "An error occured"}), 500

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
    stdout = False
    if 'STDOUT' in request.args:
        stdout = True
    return jsonify({"courses": manager.get_all_courses_data(only_stdout = stdout)})


@app.route('/courses/<course_name>/labs')
def get_labs(course_name):
    """
    Responds with with a list of labs for the specified course
    Example:GET /courses/cc451/labs
    Response body: {"labs": ["lab1_client", "lab1_server", "lab3", "lab4"]}
    """
    try:
        labs = manager.get_all_labs_data(course_name)
        return jsonify({"labs": labs}) 
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404

@app.route('/courses/<course_name>/labs/<lab_id>/lab_guide')
def get_lab_guide(course_name, lab_id):
    try:
        lab_guide_content = manager.get_lab_guide_content(course_name, lab_id)
        return jsonify({"message": "SUCCESS", 'lab_guide': lab_guide_content})
    except manager.LabHasNoGuideError:
        return jsonify({"message": "This lab does not have a guide"}), 404
    except:
        return jsonify({"message": "An error occured"}), 500

@app.route('/courses/<course_name>/labs', methods=["POST"])
def add_lab(course_name):
    try:
        lab_data = request.form.to_dict()
        if 'lab_guide' in request.files:
            manager.add_lab(course_name, lab_data, request.files['lab_guide'])
        else:
            manager.add_lab(course_name, lab_data)
        return jsonify({"message": "SUCCESS"}), 200
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404
    except manager.LabAlreadyExistsError:
        return jsonify({"message": "Lab with this name already exists"}), 400
    except manager.InvalidLabDataError:
        return jsonify({"message": "Invalid lab data"}), 400
    except:
        return jsonify({"message": "An error occured"}), 500
    pass


@app.route('/courses/<course_name>/labs/<lab_id>', methods=["PUT"])
def edit_lab(course_name, lab_id):
    try:
        lab_data = request.form.to_dict()
        manager.edit_lab(course_name, lab_data)
        return jsonify({"message": "SUCCESS"}), 200
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404
    except manager.InvalidLabDataError:
        return jsonify({"message": "Invalid lab data"}), 400
    except manager.LabNotFoundError:
        return jsonify({"message": "Lab not found"}), 404
    except:
        return jsonify({"message": "An error occured"}), 500
    pass

@app.route('/courses/<course_name>/labs/<lab_id>', methods=["DELETE"])
def delete_lab(course_name, lab_id):
    try:
        manager.delete_lab(course_name, lab_id)
        return jsonify({"message": "SUCCESS"}), 200
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404
    except:
        return jsonify({"message": "An error occured"}), 500


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
        return jsonify({"message": "course and lab query parameters must be included"}), 400
    try:
        if 'student' in request.args:
            manager.run_grader(course_name, lab_name, student=True)
        else:
            manager.run_grader(course_name, lab_name)
        return jsonify({"message": "SUCCESS"}), 200
    except:
        return jsonify({
                "message": "Failed to run the grader"
            }), 500


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
        return jsonify({"message": "course, lab and method query parameters must be included"}), 400
    if method == "file":
        if 'submissions_file' not in request.files:
            return jsonify({"message": UPLOAD_STATUS.FILE_NOT_INCLUDED.value}), 400
        submissions_file = request.files['submissions_file']
        if submissions_file.filename == '':
            return jsonify({
                "message": UPLOAD_STATUS.FILE_NOT_SELECTED.value
            }), 400
        # submissions_file will be falsy if the file is empty
        if not submissions_file:
            return jsonify({
                "message": UPLOAD_STATUS.FILE_EMPTY.value
            }), 400
        if allowed_file(submissions_file.filename):
            # TODO: secure filename
            try:
                manager.add_submissions(
                    course_name, lab_name, submissions_file)
                return jsonify({
                    "message": UPLOAD_STATUS.SUCCESS.value
                }), 200
            except:
                return jsonify({
                    "message": UPLOAD_STATUS.GRADER_FAILED.value
                }), 500
        else:
            return jsonify({
                "message": UPLOAD_STATUS.UNSUPPORTED_FILE.value
            }), 400
    elif method =="file-moss":
        if 'submissions_file' not in request.files:
            return jsonify({"message": UPLOAD_STATUS.FILE_NOT_INCLUDED.value}), 400
        submissions_file = request.files['submissions_file']
        if submissions_file.filename == '':
            return jsonify({
                "message": UPLOAD_STATUS.FILE_NOT_SELECTED.value
            }), 400
        # submissions_file will be falsy if the file is empty
        if not submissions_file:
            return jsonify({
                "message": UPLOAD_STATUS.FILE_EMPTY.value
            }), 400
        if allowed_file(submissions_file.filename):
            # TODO: secure filename
            try:
                res = manager.apply_moss(
                    submissions_file, request.form)
                return jsonify(res), 200
            except:
                return jsonify({
                    "message": UPLOAD_STATUS.GRADER_FAILED.value
                }), 500
        else:
            return jsonify({
                "message": UPLOAD_STATUS.UNSUPPORTED_FILE.value
            }), 400
    elif method == "import-google":
        access_token = request.json['accessToken']
        sheet_link = request.json['sheetLink']
        # Checks if the field parameter is included and not empty
        if 'field' in request.args and request.args.get('field'):
            importer = import_submissions.GoogleImportSubmissions(
                access_token, sheet_link, course_name, lab_name, request.args.get('field'))
        else:
            importer = import_submissions.GoogleImportSubmissions(
                access_token, sheet_link, course_name, lab_name)
        try:
            importer.import_submissions()
            return jsonify({"message": "SUCCESS"}), 200
        except:
            # TODO: handle detectable exceptions
            return jsonify({"message": "Failed to import submissions"}), 500

    elif method == "import-ms":
        access_token = request.json['accessToken']
        sheet_link = request.json['sheetLink']     
        importer = import_submissions.MSImportSubmissions(
                access_token, sheet_link, course_name, lab_name)
        try:
            importer.import_submissions()
            return jsonify({"message": "SUCCESS"}), 200
        except:
            # TODO: handle detectable exceptions
            return jsonify({"message": "Failed to import submissions"}), 500


@app.route('/courses/<course_id>/edit', methods=["GET"])
def edit_course(course_id):
    try:
        course_data = manager.get_course_data_with_test_cases(course_id)
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404
    except:
        return jsonify({"message": "An error occured"}), 500
    return jsonify(course_data)


@app.route('/courses/<course_id>', methods=["PUT"])
def update_course(course_id):
    try:
        manager.update_course_data(course_id, request.json)
    except manager.CourseNotFoundError:
        return jsonify({"message": "Course Not Found"}), 404
    except:
        return jsonify({"message": "An error occured"}), 500
    return jsonify({"message": "Course updated successfuly"})


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
        return jsonify({"message": "course, lab and type query parameters must be included"}), 400

    if results_type == "download":
        try:
            return send_file(manager.compressed_results(course_name, lab_name))
        except:
            return jsonify({
                "message": "Failed to fetch results, please make sure you run the grader first"
            }), 400

    elif results_type == "diff":
        # change it to (test_course)
        # if course_name == "test_course":
            #return jsonify(manager.run_grader_diff(course_name, lab_name)), 200
        try:
                return jsonify(manager.run_grader_diff(course_name, lab_name)), 200
                # return jsonify(manager.get_diff_results_file(course_name, lab_name)), 200
        except:
                return jsonify({
                    "message": "Failed to fetch diff results, please make sure you run the grader first"
                }), 400
    else:
        return jsonify({
            "message": "Failed to fetch results, please make sure you run the grader first"
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
            return jsonify({"message": "Invalid sheet link"}), 400
        try:
            importer.only_one_uploads_column()
            return jsonify({"message": "SUCCESS"}), 200
        except import_submissions.TooManyUploadColumnsError as e:
            fields = importer.get_url_fields()
            return jsonify({'msg': str(e), 'fields': fields}), 400
        except import_submissions.InvalidSheetError as e:
            return str(e), 400
        except:
            return jsonify({"message": "An unexpected error occured"}), 500
    elif method == 'import-ms':
        try:
            importer = import_submissions.MSImportSubmissions(
                access_token, sheet_link)
            return jsonify({"message": "SUCCESS"}), 200

        except:
            # TODO: handle detectable exceptions
            return jsonify({"message": "Invalid sheet link"}), 400




@app.route('/submissions', methods=["GET"])
def get_submission_files():
    try:
        course_name = request.args['course']
        lab_name = request.args['lab']
    except KeyError:
        return jsonify({"message": "course, lab and submission_id query parameters must be included"}), 400
    if('submission_id' in request.args):
        submission_id = request.args['submission_id']
        try:
            files_list = manager.get_submission_files(course_name, lab_name, submission_id)
            return jsonify(files_list)
        except manager.SubmissionNotFoundError:
            return jsonify({"message": "Submission not found"}), 404
        except:
            return jsonify({"message": "An error occurred"}), 500
    else:
        submissions_list = manager.get_submissions_list(course_name, lab_name)
        return jsonify(submissions_list)

@app.route('/submission_file', methods=["GET"])
def get_submission_file_content():
    try:
        course_name = request.args['course']
        lab_name = request.args['lab']
        submission_id = request.args['submission_id']
        file_name = request.args['file_name']
    except KeyError:
        return jsonify({"message": "course, lab, submission_id and file_name query parameters must be included"}), 400
    try:
        submission_file_content = manager.get_submission_file_content(course_name, lab_name, submission_id, file_name)
        return jsonify({"message": "SUCCESS", 'file_content': submission_file_content})
    except manager.SubmissionFileNotFoundError:
        return jsonify({"message": "Submission file not found"}), 404
    except:
        return jsonify({"message": "An error occurred"}), 500
    

@app.route('/submissions', methods=["PUT"])
def update_submission_file():
    try:
        course_name = request.args['course']
        lab_name = request.args['lab']
        submission_id = request.args['submission_id']
    except KeyError:
        return jsonify({"message": "course, lab and submission_id query parameters must be included"}), 400
    try:
        manager.update_submission_files(course_name, lab_name, submission_id, request.files)
        return jsonify({"message": 'Files edited successfully'})
    except manager.SubmissionNotFoundError:
        return jsonify({"message": "Submission not found"}), 404
    except:
        return jsonify({"message": 'An error occurred'}), 500

