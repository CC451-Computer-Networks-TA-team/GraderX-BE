from pathlib import Path
import json


def create_course(course_name, language, labs, current_courses):
    for course in current_courses:
        if course.lower() == course_name.lower():  
            return "Course already present", 500    

def edit_courses_config(data):
    courses_config_path = Path(__file__).parent.parent.parent.joinpath("courses_config.json")
    with open(courses_config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)