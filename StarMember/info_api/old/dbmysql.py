from flask import current_app
import random

class MemberInfo:
    def __init__(self, name = '', gid = None, age = '', sex = '', address = '', tel = '', mail = '', face = '' , img = ''):
        self.uid = uuid.uuid1().hex[2:8]
        self.name = name
        self.gid = gid
        self.age = age
        self.sex = sex
        self.address = address
        self.tel = tel
        self.mail = mail

    @property
    def BasicInfoTuple(self):
        return (self.uid, self.name, self.age, self.sex, self.address \
                , self.tel, self.mail)

    @property
    def GID(self):
        return self.gid
   

def new_id():
    return int(random.random() * 0xFFFFFF)
        
def addMember(_member_info):
    '''
        添加新的成员信息

    if 'face_img' not in request.files:
        return jsonify({'code':1422, 'data':'' ,'msg':'need face image.' })
    img_obj = request.files['face_img']
        :参数:
            _member_info    成员信息类 MemberInfo 实例

        :返回值:
            成功 True 否则返回 False
    '''
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('insert into user(UID, NAME, AGE, SEX, ADDRESS, TEL, MAIL)\
                    VALUES (%s, %s, %s, %s, %s, %s, %s)', _member_info.BasicInfoTuple);
        c.execute('insert into check_status(UID, CHECK_TIMES) values (%s, %s)', (_member_info.uid, 0))
        c.execute('insert into group_members(UID, GID) values (%s, %s)', (_member_info.uid, _member_info.GID))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return _member_info.uid


def queryMemberUIDByName(_name):
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('select UID from user where (NAME == %s)', (_name,))
        conn.commit()
        result = c.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    if not result:
        return None
    return result[0][0]


def queryMembersByGID(_gid):
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('select UID, NAME, AGE, SEX, ADDRESS, TEL, MAIL from user where (UID IN (select UID from group_members where (GID == %s)))', (_gid,))
        conn.commit()
        result = c.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return [
        {
            'uid' : uid
            , 'name' : name
            , 'age' : age
            , 'sex' : sex
            , 'address' : addr
            , 'tel' : tel
            , 'mail' : mail
        } for uid, name, age, sex, addr, tel, mail in result
    ] 

def addGroup(_name, _desp):
    '''
        添加新的组

        :参数:
            _name       小组名称
            _desp       小组描述

        :返回值:
            成功则返回新添加小组的 GID，否则返回 None
    '''
    #new_gid = uuid.uuid1().hex[2:8]
    new_gid = new_gid()
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('insert into work_group(GID, NAME, DESP) values (%s, %s, %s)', (new_gid, _name, _desp))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return new_gid


def queryNameByGID(_gid):
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('select NAME from work_group where (GID == %s)', (_gid, ))
        conn.commit()
        result = c.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    if not result:
        return None
    return result[0][0]

def queryMemberByUID(_uid):
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('SELECT UID, NAME, AGE, SEX, ADDRESS, TEL, MAIL FROM user WHERE (UID == %s)', (_uid,))
        conn.commit()
        result = c.fetchall()
    except Exception as e:
        conn.rollback()
        raise e

    if not result:
        return None

    uid, name, age, sex, address, tel, mail = result[0]
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('SELECT GID FROM group_members WHERE (UID == %s)', (_uid,))
        conn.commit()
        result = c.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return {
            'name' : name
            , 'age' : age
            , 'uid' : uid
            , 'sex' : sex
            , 'address' : address
            , 'tel': tel
            , 'mail' : mail
            , 'gid' : result[0][0]
        }


def removeMemberByUID(_uid):
    '''
        根据 UID 移除成员
    '''
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()

    try:
        c.execute('delete from user where (UID == %s) ', (_uid,))
        c.execute('delete from group_members where (UID == %s)', (_uid,))
        c.execute('delete from check_status where (UID == %s)', (_uid,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    
    return True


def removeMemberByName(_name) :
    '''
        根据 name 移除成员
    '''
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('select UID from user where (NAME == %s)', (_name,))
        conn.commit()
        raw = c.fetchall()
    except Exception as e:
        conn.rollback()
        raise e

    if not raw:
        return

    uid = raw[0][0]

    conn.begin()
    c = conn.cursor()
    try:
        c.execute('delete from user where (NAME == %s) ', (_name,))
        c.execute('delete from group_members where (UID == %s)', (uid,))
        c.execute('delete from check_status where (UID == %s)', (uid,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return True
