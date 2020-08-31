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
from io import BytesIO
import requests
import base64
from validator_collection import validators, checkers
import urllib.parse


def get_id_from_url(url):
    return re.findall(r'[-\w]{25,}', url)[0]


class ImportSubmissions(ABC):
    def __init__(self, access_token, spreadsheet_link, course=None, destination_lab=None, field=None):
        self.credentials = self.authorize(access_token)
        self.sheet = self.open_sheet(self.credentials, spreadsheet_link)
        self.course = course
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
        manager.clear_submissions(self.course, self.destination_lab)
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
        manager.save_single_submission(self.course, self.destination_lab,
                                       file_in_memory, file_name)


class MSImportSubmissions(ImportSubmissions):
    '''
    Responsible for importing submissions from a MS submission folder that holds MS form responses
    '''

    def __init__(self, access_token, source, course = None,  destination_lab=""):

        self.ENDPOINT_SHARE = 'https://graph.microsoft.com/v1.0/shares/'
        self.ENDPOINT_Drives = 'https://graph.microsoft.com/v1.0/drives'
        self.destination_lab = destination_lab
        self.headers = None
        self.authorize(access_token)
        self.course = course
        if self.get_headers():
            self.open_sheet(source)

    def authorize(self, access_token):
        self.headers={'Authorization': 'Bearer ' + access_token}


    def get_headers(self):
        return self.headers


    def get_request(self, theRequest, jsonify=True):
        result = requests.get(theRequest, headers=self.headers)
        result.raise_for_status()
        if jsonify:
            result =  result.json()
        return result


    @staticmethod
    def check_link_source(URL):
        """ checks if the link for Google or OneDrive """
        url_parsed = urllib.parse.urlparse(URL).netloc
        #url_parsed == 'docs.google.com'
        if url_parsed == 'alexuuni-my.sharepoint.com':
            return 'ms forms'
        elif url_parsed == 'docs.google.com':
            return 'google forms'
        else:
            return False


    @staticmethod
    def is_MS_link(URL):
        return MSImportSubmissions.check_link_source(URL)


    def get_column_of_submissions(self):
        column_count = self.get_column_range()
        default_sheet = 'Form1'
        column_list = []
        for i in range(0,column_count):
            theRequest = f'{self.ENDPOINT_Drives}/{self.drive_id}/items/{self.excel_id}/workbook/worksheets/{default_sheet}/Usedrange/column(column={i})?$select=text'
            result = self.get_request(theRequest)
            column_list.append(result['text'])

        self.column_list = column_list
        url_lists = [self.check_URL(col) for col in column_list]
        no_of_url_lists = url_lists.count(True)

        if  no_of_url_lists == 0:

            raise UploadColumnNotFoundError(
                    'No uploaded files column is found in the spreadsheet')
        elif  no_of_url_lists > 1:
            raise TooManyUploadColumnsError(
                    'Found more than one uploaded files column')

        return column_list[url_lists.index(True)]


    def get_source_and_drive_id(self, shareID):
        theRequest = f'{self.ENDPOINT_SHARE}/{shareID}/driveItem/'
        excel_info = self.get_request(f'{self.ENDPOINT_SHARE}/{shareID}/driveItem/')
        excel_id = excel_info['id']
        drive_id = excel_info['parentReference']['driveId']
        return excel_id, drive_id


    def check_URL(self, column):
        iterCol = iter(column)
        # skip first cell, it's a title
        next(iterCol)
        # for cell in iterCol:
        #     if checkers.is_url(cell[0]):
        #         return True
        # return False
        for cell in iterCol:
            if not checkers.is_url(cell[0]):
                return False
        return True


    def get_column_range(self):
        default_sheet = 'Form1'
        theRequest = f'{self.ENDPOINT_Drives}/{self.drive_id}/items/{self.excel_id}/workbook/worksheets/{default_sheet}/Usedrange/columnCount'
        result = self.get_request(theRequest)
        columns_number = result['value']
        return columns_number


    def open_sheet(self, spreadsheet_link):
        shareID = self.convert_URL_to_ID(spreadsheet_link)
        self.excel_id, self.drive_id = self.get_source_and_drive_id(shareID)
        # get submission_columns
        self.sub_list = self.only_one_uploads_column()


    def only_one_uploads_column(self):
        """
        Checks each column in the usedRange to count # of columns with URLs,
        """
        column_count = self.get_column_range()
        default_sheet = 'Form1'
        column_list = []
        for i in range(0,column_count):
            theRequest = f'{self.ENDPOINT_Drives}/{self.drive_id}/items/{self.excel_id}/workbook/worksheets/{default_sheet}/Usedrange/column(column={i})?$select=text'
            result = self.get_request(theRequest)
            column_list.append(result['text'])
        url_lists = [self.check_URL(col) for col in column_list]
        no_of_url_lists = url_lists.count(True)

        if  no_of_url_lists == 0:
            raise UploadColumnNotFoundError(
                    'No uploaded files column is found in the spreadsheet')
        elif  no_of_url_lists > 1:
            raise TooManyUploadColumnsError(
                    'Found more than one uploaded files column')
        
        return column_list[url_lists.index(True)]
        


    def import_submissions(self):

        submission_list = self.sub_list
        #clean directory
        #curr_dir = str(Path(__file__).parent.resolve())
        # manager.clean_directory(Path(
        #     f"{curr_dir}/courses/cc451/app/{self.destination_lab}/submissions/2020"))

        iterCol = iter(submission_list)
        next(iterCol)
        for URL in iterCol:
            self.save_to_lab(URL[0])


    def get_file_name(self, file_id, drive_id):
        theRequest = f'{self.ENDPOINT_Drives}/{drive_id}/items/{file_id}'
        result = self.get_request(theRequest)
        file_name = result['name']
        return file_name

    def save_to_lab(self, file_URL):

        shareID = self.convert_URL_to_ID(file_URL)
        file_id, drive_id = self.get_source_and_drive_id(shareID)
        file_name = self.get_file_name(file_id, drive_id)

        theRequest = f'{self.ENDPOINT_Drives}/{drive_id}/items/{file_id}/content'
        result = self.get_request(theRequest, False)
        file_in_memory = BytesIO(result.content)
        # call the manager
        manager.save_single_submission(self.course, self.destination_lab,file_in_memory, file_name)


    def convert_URL_to_ID(self, source):
        x = base64.b64encode(bytes(source,'utf-8')).decode("utf-8")
        x = 'u!' + x.replace('/','_').replace('+','-').strip('=')
        return x



class InvalidSheetError(Exception):
    pass


class EmptySecondRowError(InvalidSheetError):
    pass


class UploadColumnNotFoundError(InvalidSheetError):
    pass


class TooManyUploadColumnsError(InvalidSheetError):
    pass
