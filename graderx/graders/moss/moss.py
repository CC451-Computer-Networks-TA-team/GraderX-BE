import glob 
import subprocess
from pathlib import Path
import os

class Moss:
    def __init__(self):
        self.config = {}
        self.config['m'] = "10"
        self.config['l'] = "c"
        self.config['n'] = "250"
    
    def set_config(self, settings, files_path):
        for key in settings:
            try:
                self.config[key] = settings[key]
            except:
                pass
        self.files_path = files_path
    
    def get_config(self):
        return self.config

    def get_command(self):
        command = ['perl', str(Path(__file__).parent.joinpath('moss.pl'))]
        for key in self.config:
            if key != 'files':
                command.append('-' + key)
                command.append(self.config[key])

        actual_files = []
        files = glob.glob(str(self.files_path.resolve()) + '/**/*', recursive = True) 
        files = [f for f in files if os.path.isfile(f)]
        actual_files.extend(list(map(lambda file: os.path.relpath(file, self.files_path.resolve()), files)))

        command.extend(actual_files)
        print(" ".join(command))
        return command
        
    def get_result(self):
        result = {}
        command = self.get_command()
        opt = subprocess.run(command, cwd=self.files_path.resolve(), capture_output = True)
        
        result['error_message'] = opt.stderr.decode("utf-8")
        if opt.stderr.decode("utf-8") == '':
            result['status'] = 200
        else:
            result['status'] = 400

        opt = opt.stdout.decode("utf-8").split('\n')
        result['url'] = opt[len(opt) -2]

        return result
