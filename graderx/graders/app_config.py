from pathlib import Path


COURSES_DATA_PATH = Path(__file__).parent.joinpath("courses_config.json")
LAB_GUIDE_FILENAME = 'lab_guide.md'
MOSS_PATH = Path(__file__).parent.joinpath('moss/submissions')

# Courses config course-related variables
COURSE_NAME = 'name'
COURSE_TYPE = 'type'
COURSE_VARIANT = 'variant'
COURSE_LABS = 'labs'

# Courses config lab-related variables
LAB_NAME = 'name'
DISABLE_INTERNET = 'disable_internet'
LAB_RUNTIME_LIMIT = 'runtime_limit'
LAB_TEST_CASES = 'test_cases'
PUBLIC_TEST_CASES = 'public_test_cases'