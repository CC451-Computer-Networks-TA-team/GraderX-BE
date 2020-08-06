from . import manager
from pathlib import Path
from io import BytesIO
import requests
from abc import ABC, abstractmethod


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


class MS_Submissions(ImportSubmissions):
    '''
    Responsible for importing submissions from a MS submission folder that holds MS form responses
    '''

    def __init__(self, access_token, source,  destination_lab=""):

        self.ENDPOINT = 'https://graph.microsoft.com/v1.0/me/drive/'
        self.destination_lab = destination_lab
        self.headers = None

        self.authorize(access_token)
        if self.get_headers():
            self.download_files_from_my_drive(source)


    def authorize(self, access_token):
        self.headers = {'Authorization': 'Bearer ' + access_token}


    def get_headers(self):
        return self.headers


    def download_files_from_my_drive(self, source):

        # get folder of submissions
        self.get_source_id(source)
        # get its children
        self.import_submissions()


    def get_source_id(self, source):
        folder_url = urllib.parse.quote(source)
        result = requests.get(
            f'{self.ENDPOINT}/root:/{folder_url}', headers=self.headers)
        result.raise_for_status()
        folder_info = result.json()
        folder_id = folder_info['id']
        self.folder_id = folder_id


    def open_sheet(self, credentials, spreadsheet_link):
        pass


    def only_one_uploads_column(self):
        """
        Checks the second row of the sheet to count the number of cells with URLs that supposedly mean
        a submission link, and only passes if it has exactly one cell with a URL
        """
        pass


    def import_submissions(self):
        """
        get files list, then for every file call save_to_lab
        """

        result = requests.get(f'{self.ENDPOINT}/items/{self.folder_id}'
                              + '/children?$select=id,name', headers=self.headers)
        result.raise_for_status()
        result = result.json()

        files_list = {i['name']: i['id'] for i in result['value']}
        for t in files_list.items():
            self.save_to_lab(t)


    def get_file_content(self, file_id):
        result = requests.get(
            f'{self.ENDPOINT}/items/{file_id}/content', headers=self.headers)
        result.raise_for_status()
        return result.content


    def save_to_lab(self, file_tuple):
        """
        Takes a file id, downloads it then it calls the manager to save it in the corresponding lab

        """

        file_content = self.get_file_content(file_tuple[1])
        file_name = file_tuple[0]
        file_in_memory = BytesIO(file_content)
        manager.save_single_submission(
            self.destination_lab, file_in_memory, file_name)
