from flask import Flask
from flask import request

from config import Config

from app import doyleinfo

class DoyleStatusApp(Flask):
    def __init__(self):
        super(DoyleStatusApp,self).__init__(__name__)
        self.config.from_object(Config)

    def start(self):
        self.doyleInfo = doyleinfo.DoyleInfo()
        self.run(host='0.0.0.0',port=8080)

    def shutdown(self):
        print('Shutting down doyleinfo')
        self.doyleInfo.quit()
        print('Shutting down the server')
        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        if shutdown_func is None:
            print('Failed to get shutdown function, cannot stop')
        else:
            shutdown_func()

doyleStatusApp = DoyleStatusApp()

from app import routes

