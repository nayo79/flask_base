from flask import Flask
from logging.config import dictConfig
#from flask_restplus import Resource, Api  # swagger 사용을 위해. flask_restplus import 

# loffing config 
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
      'console': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
      },
      'file': {
        'class': 'logging.handlers.RotatingFileHandler',
        'level': 'ERROR',
        'filename': 'edge_debug.log',
        'maxBytes': 1024*1024*2,
        'backupCount': 5,
        'formatter': 'default'
      }
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['console', 'file']
    }
})

app = Flask(__name__, static_url_path='/static', instance_relative_config=True)
#api = Api(app, version='1.0', title='key search api', description='key search api')

# 추가할 모듈이 있다면 추가

# config 파일이 있다면 추가
app.config.from_pyfile('config.py', silent=True)  # 설정파일 추가 : config.py
 
# 앞으로 새로운 폴더를 만들어서 파일을 추가할 예정임
# from app.main.[파일 이름] --> app 폴더 아래에 main 폴더 아래에 [파일 이름].py 를 import 한 것임
 
# 위에서 추가한 파일을 연동해주는 역할
# app.register_blueprint(추가한 파일)

# 파일이름이 main/index.py 이므로 
from app.main.index import main as main

# 위에서 추가한 파일을 연동해주는 역화
app.register_blueprint(main)
