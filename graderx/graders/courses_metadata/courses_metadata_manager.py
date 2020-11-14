import pickle
from pathlib import Path


def load_courses_data():
    with open(Path(__file__).parent.joinpath('courses_metadata.pickle'), 'rb') as f:
        return pickle.load(f)

def get_courses_names():
    courses_data = load_courses_data()
    return [course.name for course in courses_data]

def update_courses_data(courses_data):
    with open(Path(__file__).parent.joinpath('courses_metadata.pickle'), 'wb') as f:
        pickle.dump(courses_data, f)


def get_course_by_name(course_name):
    courses_data = load_courses_data()
    try:
        requested_course = next(
            filter(lambda c: c.name.lower() == course_name.lower(), courses_data))
        return requested_course
    except StopIteration:
        raise CourseNotFoundError


def course_exists(course_name):
    try:
        get_course_by_name(course_name)
        return True
    except:
        return False


def save_course(course):
    try:
        courses_data = load_courses_data()
    except FileNotFoundError:
        courses_data = []
    courses_data.append(course)
    update_courses_data(courses_data)


def update_course(course):
    courses_data = load_courses_data()
    courses_data = list(
        filter(lambda c: c.name != course.name, courses_data)) + [course]
    update_courses_data(courses_data)


def delete_course(course):
    courses_data = load_courses_data()
    courses_data = list(filter(lambda c: c.name != course.name, courses_data))
    update_courses_data(courses_data)


class Course:
    ALLOWED_TYPES = {'stdout', 'unittest'}
    ALLOWED_VARIANTS = {'stdout': {'c'}, 'unittest': {'pytest'}}

    def __init__(self, name, variant, type_="stdout", labs=[]):
        self.set_name(name)
        self.set_type(type_)
        self.set_variant(variant)
        self.set_labs(labs)

    def validate(self):
        errors = []
        if course_exists(self.name):
            errors.append('course name must be unique')
        return errors

    def save(self, exist_ok = False):
        if course_exists(self.name):
            if not exist_ok:
                raise CourseAlreadyExists
        else:
            save_course(self)

    def update(self):
        if course_exists(self.name):
            update_course(self)
        else:
            raise CourseNotFoundError
    
    def delete(self):
        if course_exists(self.name):
            delete_course(self)
        else:
            raise CourseNotFoundError

    def get_name(self):
        return self._name

    def set_name(self, name):
        if isinstance(name, str) and len(name) < 50:
            self._name = name
        else:
            raise InvalidCourseDataError(
                'course name must be a string and has a maximum of 50 characters')

    def get_type(self):
        return self._type

    def set_type(self, type_):
        if isinstance(type_, str) and type_.lower() in self.ALLOWED_TYPES:
            self._type = type_.lower()
        else:
            raise InvalidCourseDataError(
                f"course type must one of these: {', '.join(self.ALLOWED_TYPES)}")

    def get_variant(self):
        return self._variant

    def set_variant(self, variant):
        if isinstance(variant, str) and variant.lower() in self.ALLOWED_VARIANTS[self._type]:
            self._variant = variant.lower()
        else:
            raise InvalidCourseDataError(
                f"course variant must one of these: {', '.join(self.ALLOWED_VARIANTS[self._type])}")
    
    def get_labs(self):
        return self._labs
    

    def set_labs(self, labs):
        if all([isinstance(lab, Lab) for lab in labs]) and self.__all_names_unique(labs):
            self._labs = labs
        else:
            raise InvalidCourseDataError("labs must be Lab objects and have unique names")

    def add_lab(self, lab):
        self.__check_lab_type(lab)
        if lab.name.lower() not in [lab.name.lower() for lab in self.labs]:
            self.labs.append(lab)
        else:
            raise InvalidCourseDataError("a lab with this lab's name already exists")
    
    def get_lab_by_name(self, lab_name):
        try:
            requested_lab = next(
                filter(lambda lab: lab.name.lower() == lab.lower(), self.labs))
            return requested_lab
        except StopIteration:
            raise LabNotFoundError
    
    def delete_lab(self, lab_name):
        self.labs = list(filter(lambda lab: lab.name != lab_name, self.labs))


    def __check_lab_type(self, lab):
        if isinstance(lab, Lab):
            return InvalidCourseDataError('lab must be a Lab object')

    def __all_names_unique(self, labs):
        return len(labs) == len(set([lab.name.lower() for lab in labs]))
    
    def dict_repr(self):
        return {'name': self.name, 'variant': self.variant, 'type': self.type_, 'labs': [lab.dict_repr() for lab in self.labs]}

    name = property(get_name, set_name)
    type_ = property(get_type, set_type)
    variant = property(get_variant, set_variant)
    labs = property(get_labs, set_labs)


class Lab:
    def __init__(self, name, disable_internet, runtime_limit, public_test_cases=[]):
        self.set_name(name)
        self.set_disable_internet(disable_internet)
        self.set_runtime_limit(runtime_limit)
        self.set_public_test_cases(public_test_cases)

    def get_name(self):
        return self._name

    def set_name(self, name):
        if isinstance(name, str) and len(name) < 24:
            self._name = name
        else:
            raise InvalidLabDataError(
                'lab name must be a string and has a maximum of 24 characters')

    def get_disable_internet(self):
        return self._disable_internet

    def set_disable_internet(self, disable_internet):
        if isinstance(disable_internet, bool):
            self._disable_internet = disable_internet
        elif isinstance(disable_internet, str):
            self._disable_internet = True if disable_internet == 'true' else False
        else:
            raise InvalidLabDataError('disable_internet must be a boolean')

    def get_runtime_limit(self):
        return self._runtime_limit

    def set_runtime_limit(self, runtime_limit):
        if isinstance(runtime_limit, (int, str)):
            runtime_limit = int(runtime_limit)
            if runtime_limit > 0 and runtime_limit < 6:
                self._runtime_limit = runtime_limit
            else:
                raise InvalidLabDataError("runtime_limit must be greater than 0 and less than or equal 5")
        else:
            raise InvalidLabDataError(
                'runtime_limit must be an integer or string of numbers')

    def get_public_test_cases(self):
        return self._public_test_cases

    def set_public_test_cases(self, public_test_cases):
        if isinstance(public_test_cases, list) and all([isinstance(test_case, str) for test_case in public_test_cases]):
            self._public_test_cases = public_test_cases
        else:
            raise InvalidLabDataError(
                'public test cases must be an array of strings')

    def dict_repr(self):
        return {'name': self.name, 'disable_internet': self.disable_internet,
         'runtime_limit': self.runtime_limit, 'public_test_cases': self.public_test_cases}

    name = property(get_name, set_name)
    disable_internet = property(get_disable_internet, set_disable_internet)
    runtime_limit = property(get_runtime_limit, set_runtime_limit)
    public_test_cases = property(get_public_test_cases, set_public_test_cases)


class CourseNotFoundError(Exception):
    pass

class CourseAlreadyExists(Exception):
    pass

class LabNotFoundError(Exception):
    pass

class InvalidCourseDataError(Exception):
    pass


class InvalidLabDataError(Exception):
    pass
