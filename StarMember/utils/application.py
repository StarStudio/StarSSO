from .config import ConfigMap

class ApplicationMetadata(ConfigMap):

    @staticmethod
    def FromApplicationID(_application_id):
        '''
            Load application metadata.

            :params:
                _application_id     ApplicationID

            :return:
                ApplicationMetadata Instance.
        '''
        try:
            _application_id = int(_application_id)
        except ValueError as e:
            raise ValueError('Application ID should be an integer.')
            return None

        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            affected = c.execute('select extra_meta from application where id=%s', (_application_id,))
            if affected < 1:
                conn.commit()
                raise ValueError('No such application (id = %s)' % _application_id)
            raw = c.fetchall()[0][0]
            meta = ApplicationMetadata()
            meta.raw = raw
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

        return meta


    @staticmethod
    def UpdateMetaData(_application_id, _pairs):
        '''
            Update application metadata.

            :params:
                _application_id     ApplicationID
                _pairs              ((('key1', 'key2', ... , 'keyN'), value1), ...)

            :return:
                bool, err_msg
        '''
        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            affected = c.execute('select extra_meta from application where id=%s for update', (application_id,))
            if affected < 1:
                conn.commit()
                return 'No such application (id = %s)' % application_id
            raw = c.fetchall()[0][0]
            meta = ApplicationMetadata()
            meta.raw = raw

            for key_path, value in _pairs:
                meta._delete_key(*key_path)
                if value is not None and value is not '':
                    meta._set_default(*key_path, default = value)

            affected = c.execute('update application set extra_meta=%s where id=%s', (meta.raw, application_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return 'Unexcepted error occurs : %s' % str(e)

        return None

    DEFAULT_VALUES = {}
