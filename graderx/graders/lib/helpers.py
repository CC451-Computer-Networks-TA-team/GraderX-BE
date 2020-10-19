from zipfile import ZipFile
from pathlib import Path
from datetime import datetime


def create_zip_file(results_files):
    compressed_file_path = Path(__file__).parent.joinpath(
        "compressed_results.zip")
    with ZipFile(str(compressed_file_path), 'w') as zip_obj:
        for file in results_files:
            zip_obj.write(file, arcname=file.name)
    return compressed_file_path

def current_timestamp():
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S%f")