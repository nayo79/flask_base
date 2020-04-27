#!/usr/bin/env python
# coding: utf-8

from flask import current_app as app
# pymssql 패키지 import
import pymssql
import logging


# MSSQL 접속
db_server='127.0.0.1:1433' 
db_user='test'
db_password='enertork'
db_database='miraeMS'

# db connect 
def db_connect() :
    db = pymssql.connect(server=db_server, 
                          user=db_user, 
                          password=db_password, 
                          database=db_database, 
                          charset='utf8')
    return db

# select 쿼리 실행 모듈 
def db_runQuery(query, isResult=False) :
    rowList = None
    try:
        # MSSQL 접속    
        conn = db_connect()
        cursor = conn.cursor()
        #cursor.execute("BEGIN TRANSACTION")
        cursor.execute(query)
        if isResult == True :
            rowList = cursor.fetchall()
        conn.commit()
    except Exception as e:
        logging.error('error : %s \n query : %s ', e, query)
        conn.rollback()             
    finally:        
        conn.close()
    
    return rowList

# select 쿼리 실행 모듈 
def db_connect_runQuery(conn, cursor, query, isResult=False) :
    row = None

    cursor.execute(query)
    if isResult == True :
        row = cursor.fetchall()
    
    return row

# 검색결과 : select ET_SEARCH_MAS + ET_SEARCH_PR 
def db_search_select(project, fileName) :
    #print('db_search_select')
    queryStr = r""""""
    queryStr = r"""SELECT A.SEARCH_ID, A.SEARCH_PATH, A.SEARCH_FILE, A.SEARCH_FIELD, A.SEARCH_FIELD_SIM
                        , A.SEARCH_KEYWORD, B.SEARCH_PAGE, B.SEARCH_PR, '' AS SPEC_ITEM, '' AS SPEC_VALUE 
                   FROM ET_SEARCH_MAS A 
                       JOIN ET_SEARCH_PR B
                       ON A.SEARCH_PATH = B.SEARCH_PATH
                          AND A.SEARCH_FILE = B.SEARCH_FILE
                          AND A.SEARCH_PR_ID = B.SEARCH_PR_ID                       
                   WHERE A.SEARCH_PATH = '%s' AND A.SEARCH_FILE = '%s'
                """%(project, fileName)
    logging.debug('db_search_select : %s', queryStr)
    r = db_runQuery(queryStr, True)    
    return r

# 검색결과 : select ET_SEARCH_MAS + ET_SEARCH_PR + ET_SEARCH_REG 
def db_search_all_select(project) :
    logging.debug("db_search_all_select")
    queryStr = r""""""
    queryStr = r"""SELECT A.SEARCH_ID, A.SEARCH_PATH, A.SEARCH_FILE, A.SEARCH_FIELD, A.SEARCH_FIELD_SIM
                        , A.SEARCH_KEYWORD, B.SEARCH_PAGE, B.SEARCH_PR, ISNULL(C.SPEC_ITEM, '') AS SPEC_ITEM, ISNULL(C.SPEC_VALUE, '') AS SPEC_VALUE 
                   FROM ET_SEARCH_MAS A 
                       JOIN ET_SEARCH_PR B
                       ON A.SEARCH_PATH = B.SEARCH_PATH
                          AND A.SEARCH_FILE = B.SEARCH_FILE
                          AND A.SEARCH_PR_ID = B.SEARCH_PR_ID
                       LEFT OUTER JOIN ET_SEARCH_REG C
                       ON A.SEARCH_ID = C.SEARCH_ID                    
                   WHERE A.SEARCH_PATH = '%s'
                """%(project)
    r = db_runQuery(queryStr, True)    
    return r

# 검색결과 : select  ET_SEARCH_PR 
def db_search_pr_select(project, prId) :
    logging.debug("db_search_pr_select")
    queryStr = r""""""
    queryStr = r"""SELECT A.SEARCH_PATH, A.SEARCH_FILE, A.SEARCH_PR_ID, A.SEARCH_PR
                   FROM ET_SEARCH_PR A                       
                   WHERE A.SEARCH_PATH = '%s'
                """%(project)
    if prId >= 0 :
        queryStr = queryStr + """ AND A.SEARCH_PR_ID = %d """%(prId)
    #print(queryStr)
    r = db_runQuery(queryStr, True)
    return r

# 문단 정보 insert :: ET_SEARCH_PR::SEARCH_PR_ID를 먼저 생성하고 이후 ET_EARCH_MAS 정보를 구성한다. 
def db_search_pr_insert(searchDf) :
    logging.debug("db_search_pr_insert")
    # 중복 문단제거 = searchDf 에서 page,  p_s_index, p_e_index, file, path의 중복 제거 
    subsetDf = searchDf.drop_duplicates(['page', 'p_s_index', 'p_e_index', 'file', 'path'], keep='first')
    
    insertDf = subsetDf[['path', 'file', 'page', 'paragraph']]
    
    insertDf['search_pr_id'] = -1
    
    for i in insertDf.index :
        # SEARCH_PR_ID 을 정하고(path, file 의 search_pr_id max값) Insert 한다.
        queryStr = r"""SELECT ISNULL(MAX(SEARCH_PR_ID), NULL) AS SEARCH_PR_ID FROM ET_SEARCH_PR WHERE SEARCH_PATH = '%s' AND SEARCH_FILE = '%s'""" % (insertDf.loc[i].path, insertDf.loc[i].file)
        #print(queryStr)
        r = db_runQuery(queryStr, True)
                
        # 저장된 SEARCH_PR_ID 값 + 1 
        if r != None and r[0][0] != None:
            pr_id = r[0][0] + 1
        else : 
            pr_id = 0         
        #print('pr_id = ' + str(pr_id)) 
        
        insertDf.loc[i, 'search_pr_id'] = pr_id                
        #print(i, insertDf.loc[i].path, insertDf.loc[i].file, insertDf.loc[i].search_pr_id, insertDf.loc[i].paragraph, insertDf.loc[i].page)     
        queryStr = r""""""
        queryStr = r"""INSERT ET_SEARCH_PR (SEARCH_PATH, SEARCH_FILE, SEARCH_PR_ID, SEARCH_PR, SEARCH_PAGE, RDATE, RUSER)
                        OUTPUT INSERTED.SEARCH_PR_ID
                        VALUES ( '%s', '%s', %d, N'%s', %d, GETDATE(), 'ruser' )"""%(insertDf.loc[i].path, insertDf.loc[i].file, insertDf.loc[i].search_pr_id, insertDf.loc[i].paragraph, insertDf.loc[i].page)
        #print(queryStr)                        
        r = db_runQuery(queryStr, True)
        #print('insert result =')
        #print(r)            
    return insertDf

# 문단정보 insert :: ET_SEARCH_MAS 데이터 :: ET_SEARCH_PR 데이터를 먼저 구성하고 insert 한다.
def db_search_mas_insert(searchDf) :
    logging.debug("db_search_mas_insert")
    # 중복 문단제거 = searchDf 에서 'path', 'file', 'field', 'searchWord', 'search_pr_id', 'page' 의 중복 제거 
    insertDf = searchDf.drop_duplicates(['path', 'file', 'field', 'searchWord', 'search_pr_id', 'page'], keep='first')    
    for i in insertDf.index :
        #print(insertDf.loc[i].path, insertDf.loc[i].file, insertDf.loc[i].field, insertDf.loc[i].searchWord, insertDf.loc[i].search_pr_id)
        queryStr = r""""""
        queryStr = r"""INSERT ET_SEARCH_MAS (SEARCH_PATH, SEARCH_FILE, SEARCH_FIELD, SEARCH_KEYWORD, SEARCH_PR_ID, SEARCH_FIELD_SIM, RDATE, RUSER)
                       OUTPUT INSERTED.SEARCH_PR_ID
                       VALUES ( '%s', '%s', '%s', '%s', %d, %f, GETDATE(), 'ruser' )"""%(insertDf.loc[i].path, insertDf.loc[i].file, insertDf.loc[i].field, insertDf.loc[i].searchWord, insertDf.loc[i].search_pr_id, insertDf.loc[i].fieldSim)
        #print(queryStr)
        r = db_runQuery(queryStr, True)
    return True

# ET_SEARCH_MAS 삭제 - path 별로 삭제.  :: 주의 : reg table 삭제후 삭제 search_id값
def db_search_mas_del(path) :
    logging.debug("db_search_mas_del")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r"""DELETE ET_SEARCH_MAS WHERE SEARCH_PATH = '%s'"""%(sPath)
    db_runQuery(queryStr, False)
    return True

# ET_SEARCH_REG 삭제 - path 별로 삭제.  :: 주의 : mas의 search_id 값으로 지운다.
def db_search_reg_del(path) :
    logging.debug("db_search_reg_del")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r"""DELETE ET_SEARCH_REG 
                   WHERE SEARCH_ID IN 
                         (SELECT SEARCH_ID FROM ET_SEARCH_MAS WHERE SEARCH_PATH = '%s')"""%(sPath)
    db_runQuery(queryStr, False)
    return True


# ET_SEARCH_PR 삭제 - path 별로 삭제.
def db_search_pr_del(path) :
    logging.debug("db_search_pr_del")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r"""DELETE ET_SEARCH_PR WHERE SEARCH_PATH = '%s'"""%(sPath)
    db_runQuery(queryStr, False)
    return True


# ET_SEARCH_AI_REG Insert 
def db_search_ai_reg_insert(conn, cursor, setPath, setFile, setPrId, setAiFieldId, aiSpecItem, aiSpecValue) :
    logging.debug("db_search_ai_reg_insert")
    import re
    
    rUser = "rUser"
    inFileName = re.sub(r"'", r"''", r"" + setFile)  #db - 파일명에 홀따움표 '를 ''로 변환
    # SEARCH_AI_FIELD_ID 을 정하고(path, file, prId 의 search_ai_reg_id max값) Insert 한다.
    queryStr = r"""SELECT ISNULL(MAX(SEARCH_AI_REG_ID), NULL) AS SEARCH_AI_REG_ID 
                   FROM ET_SEARCH_AI_REG 
                   WHERE SEARCH_PATH = '%s' AND SEARCH_FILE = '%s' 
                         AND SEARCH_PR_ID = %d AND SEARCH_AI_FIELD_ID = %d """% (setPath, inFileName, int(setPrId), int(setAiFieldId))
    #print(queryStr)
    r = db_connect_runQuery(conn, cursor, queryStr, True)
                
    # 저장된 SEARCH_AI_FIELD_ID 값 + 1 
    if r != None and r[0][0] != None:
        ai_reg_id = r[0][0] + 1
    else : 
        ai_reg_id = 0         
    #print('ai_reg_id = ' + str(ai_reg_id)) 
                 
    #print(path, file, prId, aiField, aiFieldSim)     
    queryStr = r""""""
    queryStr = r"""INSERT ET_SEARCH_AI_REG (SEARCH_PATH, SEARCH_FILE, SEARCH_PR_ID, SEARCH_AI_FIELD_ID, SEARCH_AI_REG_ID, AI_SPEC_ITEM, AI_SPEC_VALUE, RDATE, RUSER)
                    OUTPUT INSERTED.SEARCH_AI_REG_ID
                    VALUES ( '%s', '%s', %d, %d, %d, '%s', '%s', GETDATE(), '%s' ) """%(setPath, inFileName, int(setPrId), int(setAiFieldId), int(ai_reg_id), aiSpecItem, aiSpecValue, rUser)
    logging.debug(queryStr)                        
    r = db_connect_runQuery(conn, cursor, queryStr, True)    
    #print('insert ET_SEARCH_AI_REG result =',r)
    return r

# ET_SEARCH_AI_REG 삭제 - path 별로 삭제.
def db_search_ai_reg_del(path) :
    logging.debug("db_search_ai_reg_del")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r"""DELETE ET_SEARCH_AI_REG WHERE SEARCH_PATH = '%s'"""%(sPath)
    db_runQuery(queryStr, False)
    return True

# ET_SEARCH_AI_FIELD Insert 
def db_search_ai_field_insert(conn, cursor, path, file, prId, aiField, aiFieldSim) :
    logging.debug("db_search_ai_field_insert")
    import re
    
    ai_field_id = 0
    r = []
    inFileName = re.sub(r"'", r"''", r"" + file)  #db - 파일명에 홀따움표 '를 ''로 변환
    # SEARCH_AI_FIELD_ID 을 정하고(path, file, prId 의 search_ai_field_id max값) Insert 한다.
    queryStr = r"""SELECT ISNULL(MAX(SEARCH_AI_FIELD_ID), NULL) AS SEARCH_AI_FIELD_ID FROM ET_SEARCH_AI_FIELD WHERE SEARCH_PATH = '%s' AND SEARCH_FILE = '%s' AND SEARCH_PR_ID = %d """ %(path, inFileName, int(prId))
    logging.debug(queryStr)
    r = db_connect_runQuery(conn, cursor, queryStr, True)
    #print(r)            
    # 저장된 SEARCH_AI_FIELD_ID 값 + 1 
    if r != None and r[0][0] != None:
        ai_field_id = r[0][0] + 1
    else : 
        ai_field_id = 0         
    #print('pr_id = ' + str(ai_field_id)) 
                 
    #print(path, file, prId, aiField, aiFieldSim)     
    queryStr = r""""""
    queryStr = r"""INSERT ET_SEARCH_AI_FIELD (SEARCH_PATH, SEARCH_FILE, SEARCH_PR_ID, SEARCH_AI_FIELD_ID, SEARCH_AI_FIELD, SEARCH_AI_FIELD_SIM, RDATE, RUSER)
                   VALUES ( '%s', '%s', %d, %d, '%s', %f, GETDATE(), 'ruser' )"""%(path, inFileName, prId, ai_field_id, aiField, aiFieldSim)
    logging.debug(queryStr)                        
    db_connect_runQuery(conn, cursor, queryStr, False)
    #print('insert result =')
    #print(rl)   
    return True

# ET_SEARCH_AI_FIELD 삭제 - path 별로 삭제.
def db_search_ai_field_del(path) :
    logging.debug("db_search_ai_field_del")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r"""DELETE ET_SEARCH_AI_FIELD WHERE SEARCH_PATH = '%s'"""%(sPath)
    db_runQuery(queryStr, False)
    return True


# ET_SEARCH_AI_FIELD SELECT - path/pr_id 
# return df = ['getPath', 'getFile', 'getPrId', 'getAiFieldId', 'getAiField', 'getPara']
def db_search_ai_field_select(path, prId = -1) :
    logging.debug("db_search_ai_field_select")
    queryStr = r""""""
    queryStr = r"""SELECT B.SEARCH_PATH, B.SEARCH_FILE, B.SEARCH_PR_ID, C.SEARCH_AI_FIELD_ID, C.SEARCH_AI_FIELD, B.SEARCH_PR
                   FROM ET_SEARCH_PR B                        
                        JOIN ET_SEARCH_AI_FIELD C
                        ON B.SEARCH_PATH = C.SEARCH_PATH
                            AND B.SEARCH_FILE = C.SEARCH_FILE
                            AND B.SEARCH_PR_ID = C.SEARCH_PR_ID
                   WHERE 1=1
               """
    if(path != "") :                 
        queryStr = queryStr + """ AND B.SEARCH_PATH = '%s'"""%(path)
    if(prId != -1) :                 
        queryStr = queryStr + """ AND B.SEARCH_PR_ID = %d"""%(prId) 

    #queryStr = queryStr + """ """
    r = db_runQuery(queryStr, True)
    return r


# ET_SEARCH_AI_FIELD SELECT - path/pr_id 
# return df = ['search_id','path', 'file', 'page', 'paragraph', 'keyword', 'field', 'ai_field', 'ai_sim']
def db_search_ai_field_sim_select(path, prId) :
    logging.debug("db_search_ai_field_sim_select")
    queryStr = r""""""
    queryStr = r"""SELECT A.SEARCH_ID, A.SEARCH_PATH, A.SEARCH_FILE, B.SEARCH_PAGE, B.SEARCH_PR, A.SEARCH_KEYWORD, A.SEARCH_FIELD,  C.SEARCH_AI_FIELD, C.SEARCH_AI_FIELD_SIM
                   FROM ET_SEARCH_MAS A
                        JOIN ET_SEARCH_PR B
                        ON A.SEARCH_PATH = B.SEARCH_PATH
                            AND A.SEARCH_FILE = B.SEARCH_FILE
                            AND A.SEARCH_PR_ID = B.SEARCH_PR_ID
                        JOIN ET_SEARCH_AI_FIELD C
                        ON A.SEARCH_PATH = C.SEARCH_PATH
                            AND A.SEARCH_FILE = C.SEARCH_FILE
                            AND A.SEARCH_PR_ID = C.SEARCH_PR_ID
                   WHERE 1=1
               """
    if(path != "") :                 
        queryStr = queryStr + """ AND A.SEARCH_PATH = '%s'"""%(path)
    if(prId != -1) :                 
        queryStr = queryStr + """ AND A.SEARCH_PR_ID = %d"""%(prId)

    #queryStr = queryStr + """ """
    r = db_runQuery(queryStr, True)
    return r

# ET_SEARCH_REG 읽기
def db_search_reg_select(searchId) :
    import numpy as np
    logging.debug("db_search_reg_select")

    queryStr = r"""SELECT SPEC_ITEM, SPEC_VALUE FROM ET_SEARCH_REG 
                    WHERE SEARCH_ID = %d""" %(searchId)
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)
    #print(r)

    list_r = []
    if r :
        array_r = np.array(r)[:,0]
        list_r = array_r.tolist()

    return list_r

# ET_SEARCH_REG 저장
def db_search_reg_insert(specDf) :
    logging.debug("db_search_reg_insert")
    
    insertDf = specDf.drop_duplicates(['search_id', 'specItem', 'specValue'], keep='first')    
    for i in insertDf.index :
        search_id = insertDf.loc[i].search_id
        spec_item = insertDf.loc[i].specItem
        spec_value = insertDf.loc[i].specValue
        print('spec value :', search_id, spec_item, spec_value)            
        # SEARCH_REG_ID 을 정하고(SEARCH_ID key) Insert 한다.
        queryStr = r""" SELECT ISNULL(MAX(SEARCH_REG_ID), NULL) AS SEARCH_REG_ID FROM ET_SEARCH_REG 
                        WHERE SEARCH_ID = %d """ %(search_id)
        #print(queryStr)
        r = db_runQuery(queryStr, True)
            
        # 저장된 SEARCH_REG_ID 값 + 1 
        if r != None and r[0][0] != None:
            reg_id = r[0][0] + 1
        else : 
            reg_id = 0         
        #print('pr_id = ' + str(pr_id))                   

        queryStr = r""""""
        queryStr = r"""INSERT ET_SEARCH_REG (SEARCH_ID, SEARCH_REG_ID, SPEC_ITEM, SPEC_VALUE, RDATE, RUSER)
                        OUTPUT INSERTED.SEARCH_ID
                        VALUES ( %d, %d, '%s', '%s', GETDATE(), 'ruser' )"""%(search_id, reg_id, spec_item, spec_value)
        logging.debug(queryStr)                        
        r = db_runQuery(queryStr, True)
        
    return True


# 문단정보 insert :: ET_FIELD_INFO 데이터
def db_field_info_insert(key, ai_keyword, ai_keyword_type, use_yn) :
    logging.debug("db_field_info_insert")       
    for s in ai_keyword :        
        queryStr = r""""""
        queryStr = r"""INSERT ET_FIELD_INFO (SEARCH_FIELD, SEARCH_KEYWORD, SEARCH_KEYWORD_TYPE, KEYWORD_SIM, KEYWORD_USE_YN, RDATE, RUSER)
                       OUTPUT INSERTED.SEARCH_KEYWORD
                       VALUES ( '%s', '%s', '%s', %f, '%s', GETDATE(), 'admin' )"""%(key, s[0], ai_keyword_type, (float(s[1]) * 100), use_yn)
        r = db_runQuery(queryStr, True)
    return True


# 문단정보 insert :: ET_FIELD_INFO 데이터
def db_field_info_select(field="", keywordUseYn="1") :
    logging.debug("db_field_info_select")
    queryStr = r"""SELECT SEARCH_FIELD, SEARCH_KEYWORD, SEARCH_KEYWORD_TYPE, KEYWORD_SIM, KEYWORD_USE_YN 
                   FROM ET_FIELD_INFO
                   WHERE 1 = 1
                """
    if(field != "") :
        queryStr = queryStr + """ AND SEARCH_FIELD = '%s' """ %(field)
    if(keywordUseYn != "A") :  # keywordUseYn : ALL = "A", 사용 =  "1", 미사용 = "0"
        queryStr = queryStr + """ AND KEYWORD_USE_YN = '%s' """ %(keywordUseYn)
    queryStr = queryStr + """ ORDER BY SEARCH_FIELD, SEARCH_KEYWORD_TYPE, KEYWORD_SIM, SEARCH_KEYWORD"""
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)
    
    return r

# 정규식 데이터 읽어오기 : ET_FIELD_REG 
def db_field_reg_select(field) :
    logging.debug("db_field_reg_select")
    queryStr = r"""SELECT SPEC_ITEM_REG, SPEC_VALUE_REG FROM ET_FIELD_REG WHERE SEARCH_FIELD = '%s'""" %(field)    
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)

    return r


# AI 학습 데이터 읽어오기 : ET_AI_DATA 
def db_ai_data_select() :
    logging.debug("db_ai_data_select")
    queryStr = r""" SELECT ID, SEARCH_FIELD, SEARCH_PR FROM ET_AI_DATA """
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)

    return r

# AI 학습 데이터 저장 : ET_AI_DATA
def db_ai_data_insert(path, fileName, page, field, pr, user):
    logging.debug("db_ai_data_insert")
    queryStr = r""""""
    queryStr = r"""INSERT ET_AI_DATA (SEARCH_PATH, SEARCH_FILE, SEARCH_PAGE, SEARCH_FIELD, SEARCH_PR, AI_LEARNING_YN, AI_LEARNING_DATE, RDATE, RUSER)
                   OUTPUT INSERTED.FILE_ID                 
                   VALUES ( '%s', '%s', %d, '%s', '%s', 'N', null, GETDATE(), '%s' )"""%(path, fileName, page, field, pr, user)
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)
    
    return r

# 20.03.30 페이지 정보 추가 : curr_page, total_page
# ET_PROJECT 
def db_project_insert(path, fileName, search_file_cnt, total_file_cnt, curr_page, total_page, search_status, user="user") :
    #import re
    logging.debug("db_project_insert")
    #inFileName = re.sub(r"'", r"''", r"" + fileName)  #db - 파일명에 홀따움표 '를 ''로 변환
    queryStr = r""""""
    queryStr = r"""INSERT ET_PROJECT (SEARCH_PATH, SEARCH_FILE, SEARCH_FILE_CNT, SEARCH_TOTAL_CNT, CURR_PAGE, TOTAL_PAGE, SEARCH_STATUS, RDATE, RUSER)  
                   OUTPUT INSERTED.FILE_ID                 
                   VALUES ( '%s', '%s', %d, %d, %d, %d, '%s', GETDATE(), '%s' )"""%(path, fileName, search_file_cnt, total_file_cnt, curr_page, total_page, search_status, user)
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)

    return r

# 20.03.30 페이지 정보 추가 : curr_page
def db_project_update(file_id, status, curr_page, user) :
    logging.debug("db_project_update")
    
    queryStr = r""""""
    queryStr = r""" UPDATE ET_PROJECT 
                    SET SEARCH_STATUS = '%s', 
                        CURR_PAGE = %d                        
                    WHERE FILE_ID = CONVERT(DECIMAL(18, 0),'%s') """%(status, curr_page, file_id)
    print(queryStr)
    r = db_runQuery(queryStr, False)

    return r
    
def db_project_del(path) :
    logging.debug("db_project_del")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r"""DELETE ET_PROJECT WHERE SEARCH_PATH = '%s'"""%(sPath)
    db_runQuery(queryStr, False)
    return True

# 저장 프로젝트 리스트 및 검색결과 상태값 확인.
def db_project_select(path) :
    logging.debug("db_project_select")
    sPath = "spath"
    if(path != "") :
        sPath = path
    queryStr = r""""""
    queryStr = r""" SELECT FILE_ID, SEARCH_PATH, SEARCH_FILE, SEARCH_FILE_CNT, SEARCH_TOTAL_CNT, SEARCH_STATUS
                           , CONVERT(VARCHAR(10), RDATE, 120) AS DATE, RUSER
                    FROM ET_PROJECT """
    if(path != "") :                      
        queryStr = queryStr + r""" WHERE SEARCH_PATH = '%s' """%(sPath)
        
    queryStr = queryStr + """ ORDER BY SEARCH_PATH, SEARCH_FILE """
    logging.debug(queryStr)
    r = db_runQuery(queryStr, True)

    return r

