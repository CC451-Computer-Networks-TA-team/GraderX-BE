from zipfile import ZipFile
from pathlib import Path
from enum import Enum


class GRADER_TYPES(Enum):
    UNITTEST = "unittest"
    STDOUT = "stdout"

class GRADER_VARIANTS(Enum):
    C = "c"
    PYTEST = "pytest"

class GRADER_LANGUAGES(Enum):
    C = "c"
    PYTHON = "python"


def create_zip_file(results_files):
    compressed_file_path = Path(__file__).parent.joinpath(
        "compressed_results.zip")
    with ZipFile(str(compressed_file_path), 'w') as zip_obj:
        for file in results_files:
            zip_obj.write(file, arcname=file.name)
    return compressed_file_path
