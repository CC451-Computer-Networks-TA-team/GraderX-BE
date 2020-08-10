from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import gspread
from . import manager
from validator_collection.checkers import is_url
from pathlib import Path
import random
import string
import io
import re
from abc import ABC, abstractmethod


def get_id_from_url(url):
    return re.findall(r'[-\w]{25,}', url)[0]


class ImportSubmissions(ABC):
    def __init__(self, access_token, spreadsheet_link, destination_lab=None, field=None):
        self.credentials = self.authorize(access_token)
        self.sheet = self.open_sheet(self.credentials, spreadsheet_link)
        self.destination_lab = destination_lab
        self.field = field
        super().__init__()

    @abstractmethod
    def authorize(self, access_token):
        pass

    @abstractmethod
    def open_sheet(self, credentials, spreadsheet_link):
        pass

    @abstractmethod
    def only_one_uploads_column(self):
        """
        Checks the second row of the sheet to count the number of cells with URLs that supposedly mean
        a submission link, and only passes if it has exactly one cell with a URL
        """
        pass

    @abstractmethod
    def import_submissions(self):
        """
        Finds the column with the URLs, then for every URL call __save_to_lab with that URL
        """
        pass

    @abstractmethod
    def save_to_lab(self, file_url):
        """
        Takes a file URL, downloads it then it calls the manager to save it in the corresponding lab
        """
        pass


class GoogleImportSubmissions(ImportSubmissions):
    '''
    Responsible for importing submissions from a google sheet that holds google form responses
    '''

    # def __init__(self, access_token, sheet_link, destination_lab=None):
    #     self.credentials = Credentials(access_token)
    #     gc = gspread.authorize(self.credentials)
    #     self.sheet = gc.open_by_url(sheet_link).get_worksheet(0)
    #     self.destination_lab = destination_lab

    def authorize(self, access_token):
        return Credentials(access_token)

    def open_sheet(self, credentials, spreadsheet_link):
        gc = gspread.authorize(self.credentials)
        return gc.open_by_url(spreadsheet_link).get_worksheet(0)

    def only_one_uploads_column(self):
        '''
        Checks if the spreadsheet has only one column with file uploads (supposedly submissions)
        if not, raise the corresponding exception
        '''
        sheet_second_row = self.sheet.row_values(2)
        if sheet_second_row:
            url_cells_count = list(
                map(lambda cell: is_url(cell), sheet_second_row)).count(True)

            if url_cells_count == 0:
                raise UploadColumnNotFoundError(
                    'No uploaded files column is found in the spreadsheet')
            elif url_cells_count > 1:
                raise TooManyUploadColumnsError(
                    'Found more than one uploaded files column')
        else:
            raise EmptySecondRowError('Second row of the sheet is empty')

    def get_url_fields(self):
        sheet_second_row = self.sheet.row_values(2)
        # getting the indexes of the url fields in the sheet, adding 1 because indexing in sheet starts from 1
        url_fields_indexes = [index+1 for index,
                              cell in enumerate(sheet_second_row) if is_url(cell)]
        return list(map(lambda index: self.sheet.cell(1, index).value, url_fields_indexes))

    def import_submissions(self):
        """
        Traverses the uploads column one by one, saves them in the given lab submissions folder
        """
        # Clean the destination submissions directory
        curr_dir = str(Path(__file__).parent.resolve())
        manager.clean_directory(Path(
            f"{curr_dir}/courses/cc451/app/{self.destination_lab}/submissions/2020"))
        if self.field:
            uploads_column = self.sheet.row_values(1).index(self.field)
            sheet_uploads_col = self.sheet.col_values(uploads_column+1)
        else:
            sheet_second_row = self.sheet.row_values(2)
            uploads_column = list(
                map(lambda cell: is_url(cell), sheet_second_row)).index(True)
            sheet_uploads_col = self.sheet.col_values(uploads_column+1)
        for i in range(1, len(sheet_uploads_col)):
            self.save_to_lab(sheet_uploads_col[i])

    def save_to_lab(self, file_url):
        file_id = get_id_from_url(file_url)
        drive_service = build('drive', 'v3', credentials=self.credentials)
        # Call the Drive v3 API
        request = drive_service.files().get_media(fileId=file_id)
        file_in_memory = io.BytesIO()
        downloader = MediaIoBaseDownload(file_in_memory, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        file_name = drive_service.files().get(
            fileId=file_id).execute()['name']
        manager.save_single_submission(self.destination_lab,
                                       file_in_memory, file_name)


class InvalidSheetError(Exception):
    pass


class EmptySecondRowError(InvalidSheetError):
    pass


class UploadColumnNotFoundError(InvalidSheetError):
    pass


class TooManyUploadColumnsError(InvalidSheetError):
    pass
