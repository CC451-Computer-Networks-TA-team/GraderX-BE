from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

from graderx import views
