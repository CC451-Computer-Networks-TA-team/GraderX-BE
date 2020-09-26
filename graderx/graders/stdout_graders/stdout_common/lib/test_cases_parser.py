import re
from pathlib import Path


def get_test_cases(lab_path):
    test_cases = []
    pattern = re.compile('_in$')
    for f in lab_path.joinpath('test_cases').iterdir():
        if f.is_file and pattern.search(f.name):
            test_case_id = f.name.split('_')[0]
            test_case_in = f.read_text()
            test_case_out = lab_path.joinpath(
                f'test_cases/{test_case_id}_out').read_text()
            test_cases.append((test_case_id, test_case_in, test_case_out))
    return test_cases
