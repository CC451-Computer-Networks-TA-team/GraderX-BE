from pathlib import Path
import os
import sys

def compute_total_result(result_dict, lab_abs_path):
    grades_summary = {}
    for key, val in result_dict.items():
        grade = compute_total_result_by_id(val)
        grades_summary[key] = grade
        failed_report = get_failed_cases(val['failed'])
        content = format_content(grade, failed_report)
        path = get_path(lab_abs_path, key)
        write_internal_report(content, path)

    write_summary_report(grades_summary, lab_abs_path)


def get_failed_cases(fail_data):
    data = ''
    for i in fail_data:
        data += '-'*10
        data += f"\ntest case id: {i['tc_id']}\ndifference: {i['diff']}\n"
    return data


def compute_total_result_by_id(id_obj):
    passed = len(id_obj['passed'])
    failed = len(id_obj['failed'])
    grade = round(passed/(passed + failed) * 100 , 2)
    return grade


def get_path(lab_abs_path, student_id ):
    
    the_path = lab_abs_path.joinpath('submissions').joinpath(student_id)
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


def write_summary_report(content, path):
    file_name = path.joinpath(f'{get_lab_name(path)}_result_summary.txt')
    pass_percentage = get_pass_percentage(content)
    
    if not os.path.exists(path):
        os.makedirs(path)

    with open(file_name, 'w') as out_file:
        out_file.write(f'* {get_lab_name(path)} Result Summary\n')
        out_file.write(f'--'*10 + '\n')
        out_file.write(f'* Pass Percentage: {pass_percentage}\n')

        for k,v in content.items():
            out_file.write(f'{k}:{v}\n')


def get_pass_percentage(grades_summary):
    pass_threshold = 50
    passed = len([grade for grade in grades_summary.values() if grade>pass_threshold])
    percent = round(passed/len(grades_summary) * 100, 2)
    return percent


def format_content(grade, failed_reports):
    return f'* Total Grade: {grade}\n* Failed Test Cases:\n{failed_reports}'
