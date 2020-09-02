import glob 
import subprocess

class Moss:
    def __init__(self):
        self.config = {}
        self.config['m'] = "10"
        self.config['l'] = "c"
        # self.config['d'] = "false"
        self.config['x'] = "0"
        self.config['c'] = ""
        self.config['n'] = "250"
        self.config['bindex'] = "0"
        self.config['files'] = []
    
    def set_config(self, settings):
        for key in settings:
            self.config[key] = settings[key]
    
    def get_config(self):
        return self.config

    def get_command(self):
        command = ['perl', 'moss.pl']
        input_name = []
        for key in self.config:
            if key != 'files':
                command.append('-' + key)
                command.append(self.config[key])
            else:
                for file_name in self.config[key]:
                    input_name.append(file_name)

        actual_files = []
        for dicr in input_name:
            files = glob.glob(dicr + '/**/*', recursive = True) 
            actual_files.extend(files)

        command.extend(actual_files)
        return command
        
    def get_result(self):
        result = {}
        command = self.get_command()
        opt = subprocess.run(command, capture_output = True)
        
        result['error_message'] = opt.stderr.decode("utf-8")
        if opt.stderr.decode("utf-8") == '':
            result['status'] = 200
        else:
            result['status'] = 400

        opt = opt.stdout.decode("utf-8").split('\n')
        result['url'] = opt[len(opt) -2]

        return result
