from pathlib import Path
import os
import sys
import json


pass_threshold = 50


def compute_total_result(submissions_list, lab_abs_path, key):
    """
    generates some analysis for the submissions list
    """
    grades_summary = {}
    for item in submissions_list:
        grade = compute_total_result_by_id(item)
        grades_summary[item['id']] = grade
        failed_report = get_failed_cases(item['failed'])
        content = format_content(grade, failed_report)
        path = get_path(lab_abs_path, item['id'], key)
        write_internal_report(content, path)
    # TODO: make write diff/chart consistant
    write_diff_json(submissions_list, lab_abs_path, key)
    write_chart_json(submissions_list, lab_abs_path, grades_summary, key)
    write_summary_report(grades_summary, lab_abs_path, key)


def handle_grades(id):

    pass


def get_failed_cases(fail_data):
    """
    takes submissions_list[i]['failed']
    """
    data = ''
    for i in fail_data:
        data += '-'*10
        data += f"\ntest case id: {i['tc_id']}\ndifference: {i['expected']}\n"
    return data


def compute_total_result_by_id(id_obj):
    """ 
        take one element from the submission list
        returns grade (percentage)
    """
    passed = len(id_obj['passed'])
    failed = len(id_obj['failed'])
    grade = round(passed/(passed + failed) * 100, 2)
    return grade


def get_path(lab_abs_path, student_id, key):

    the_path = lab_abs_path.joinpath(f'submissions/{key}').joinpath(student_id)
    return the_path


def get_lab_name(lab_abs_path):
    LAB_NAME = os.path.split(lab_abs_path)
    return LAB_NAME[-1]


def write_internal_report(content, path):
    file_name = path.joinpath(f'{get_lab_name(path)}_results.txt')
    if not os.path.exists(path):
        os.makedirs(path)
    with open(file_name, 'w') as out_file:
        out_file.write(content)


def write_summary_report(content, path, key):
    file_name = path.joinpath(f'/submissions/{key}/{get_lab_name(path)}_result_summary.txt')
    pass_percentage = get_pass_percentage(content)

    if not os.path.exists(path):
        os.makedirs(path)

    with open(file_name, 'w') as out_file:
        out_file.write(f'* {get_lab_name(path)} Result Summary\n')
        out_file.write(f'--'*10 + '\n')
        out_file.write(f'* Pass Percentage: {pass_percentage}\n')

        for k, v in content.items():
            out_file.write(f'{k}:{v}\n')


def get_pass_percentage(grades_summary):
    passed = len([grade for grade in grades_summary.values()
                  if grade > pass_threshold])
    percent = round(passed/len(grades_summary) * 100, 2)
    return percent


def format_content(grade, failed_reports):
    return f'* Total Grade: {grade}\n* Failed Test Cases:\n{failed_reports}'


def write_diff_json(submissions_list, path, key):
    diff_list = [{"id": item["id"], "failed":item["failed"]}
                 for item in submissions_list]
    diff_json = json.dumps(diff_list)

    file_name = path.joinpath(f'/submissions/{key}/{get_lab_name(path)}_diff_result.json')
    if not os.path.exists(path):
        os.makedirs(path)

    with open(file_name, 'w') as out_file:
        out_file.write(diff_json)


def write_chart_json(submissions_list, path, grades_summary, key):
    chart_json = get_charts_json(submissions_list, grades_summary)
    file_name = path.joinpath(f'/submissions/{key}/{get_lab_name(path)}_chart_result.json')
    if not os.path.exists(path):
        os.makedirs(path)

    with open(file_name, 'w') as out_file:
        out_file.write(chart_json)


def get_charts_json(submissions_list, grades_summary):

    # passed test cases
    passed = [i.get('passed') for i in submissions_list]
    passed = [item for l in passed for item in l]
    passed_list = [{"tc_id": k, "pass-percentage": passed.count(k)/len(grades_summary)*100}
                   for k in list(set(passed))]

    # students pass percentage
    students_list = [{"id": k, "grade": v}
                     for k, v in grades_summary.items()]
    chart = {
        'passed_tc': passed_list,
        'students_list': students_list
    }

    return json.dumps(chart)
