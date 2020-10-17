from datetime import datetime

def current_timestamp():
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S%f")