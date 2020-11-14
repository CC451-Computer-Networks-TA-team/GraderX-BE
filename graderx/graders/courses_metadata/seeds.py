# from courses_config_manager import Course, Lab
import courses_metadata_manager

lab1_client = courses_metadata_manager.Lab('lab1_client', False, 2)
lab1_server = courses_metadata_manager.Lab('lab1_server', False, 2)
lab3 = courses_metadata_manager.Lab('lab3', False, 2)
lab4 = courses_metadata_manager.Lab('lab4', False, 2)

cc451 = courses_metadata_manager.Course('cc451', 'pytest', 'unittest', [lab1_client, lab1_server, lab3, lab4])

lab1 = courses_metadata_manager.Lab('lab1', False, 2)
lab2 = courses_metadata_manager.Lab('lab2', False, 2)
lab3 = courses_metadata_manager.Lab('lab3', False, 2)

test_course = courses_metadata_manager.Course('test_course', 'c', 'stdout', [lab1, lab2, lab3])

cc451.save(exist_ok= True)
test_course.save(exist_ok = True)