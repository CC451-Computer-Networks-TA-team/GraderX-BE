import shutil
import os
import patoolib


def clean_directory(dir):
    files = dir.glob('*')
    for f in files:
        if f.is_dir():
            shutil.rmtree(str(f))
        else:
            f.unlink()


def extract_file(file_path, verbosity = -1):
    patoolib.extract_archive(
        file_path, outdir=file_path.parent, verbosity = verbosity, interactive = False)
    os.remove(file_path)


def extract_submissions(dest_directory, submissions_file,  verbosity = 0, clean_before_extraction=True):
    """
    Args:
    dest_directory: Path. Submission directory found in [lab_name]/config.py
    submissions_file: FileStorage. It is used by the request object to represent uploaded files. 

    Returns: bool
    status: True on sucessful extraction

    Actions:
    extracts the submissions file in the destenation directory and removes the rar (or Whatever) file

    """

    file_name = submissions_file.filename
    # clean the submissions directory, if it doesn't exist create it along with missing parents
    if dest_directory.exists():
        if clean_before_extraction:
            clean_directory(dest_directory)
    else:
        dest_directory.mkdir(parents = True)

    submissions_file.save(dst=(dest_directory.joinpath(file_name)))
    file_path = dest_directory.joinpath(file_name)
    try:
        extract_file(file_path)
        print("***[Success]: File extracted successfully")
    except:
        print("***[Error]: Archive is damaged")
        raise ArchiveDamagedError


class ArchiveDamagedError(Exception):
    pass
