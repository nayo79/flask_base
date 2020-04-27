import json
import pandas as pd
import numpy as np
import re
import importlib
import shutil
from werkzeug import secure_filename
from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify
from flask import current_app as app
import logging

# 추가할 모듈이 있다면 추가
import app.main.db_pymaria as madb

main = Blueprint('main', __name__, url_prefix='/')

@main.route('/', methods=['GET'])
def root():
    logging.info('root start')
    return render_template('/main/index_template.html')

@main.route('/login', methods=['GET'])
def login():
    logging.info('login start')
    return render_template('/main/signin.html')

@main.route('/modelSet', methods=['GET'])
def modelSet():
    return render_template('/main/modelSet.html')
  
@main.route('/trainSet', methods=['GET'])
def trainSet():      
    return render_template('/main/trainSet.html')
  
@main.route('/use1', methods=['GET'])
def use1():      
    return render_template('/main/use1.html')
  
@main.route('/test_tables', methods=['GET'])
def test_tables():      
    return render_template('/main/test_tables.html')
  
@main.route('/test_graph', methods=['GET'])
def test_graph():      
    return render_template('/main/test_graph.html')

# 파일 업로드 테스트.
@main.route('/trainSet/upload', methods=['POST'])
def trainSetUpload():
    print("trainSet/upload")
    f = request.files['file']  # request.args.get('file', "")
    f.save('templates/upload/' + secure_filename(f.filename))
        
    print(f.filename)
    return 'ok upload'

# train.py 소스를 서버에 복사하고 해당 소스를 import 및 실행 
# 주의 : 서버로 소스 복사시 flask가 debug 모드이면 py파일이 변경되면서 
#        자동으로 서버 리로딩 되므로 run.py 에서 app.debug = True 주석처리해야함!
#        (importlib.reload 실행)
# 테스트 : http://localhost:9999/trainRun?pyfile=train.py
@main.route('/trainRun', methods=['GET', 'POST'])
def trainUpload():    
    f = request.args['pyfile']  # request.args.get('file', "")
    print("trainRun : filename=" + f)
    
    # "templates/runpy/test.py" 경로에 실행해야할 소스파일 경로가 적용되어야한다.
    shutil.copyfile("templates/runpy/test.py", "templates/runpy/" + f)    
    
    import templates.runpy.train as pyfile
    importlib.reload(pyfile)
    pyfile.train()
    del pyfile

    return 'ok trainRun'

