import pymysql

class MySQLManager:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.conn = None

    def connect(self):
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            cursorclass=pymysql.cursors.DictCursor
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def get_users(self):
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT User, Host FROM mysql.user")
                return cursor.fetchall()
        finally:
            self.close()

    def get_databases(self):
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                dbs = cursor.fetchall()
                # Filter out standard system dbs to make it cleaner, or keep them.
                # Usually we don't want to mess with information_schema, etc.
                filtered_dbs = [db['Database'] for db in dbs]
                return filtered_dbs
        finally:
            self.close()

    def create_user(self, new_user, new_password, host='%'):
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                # Basic sanitation for username/host to prevent trivial injection if exposed
                # But mostly relying on admin usage.
                # Using f-string for DCL statements as pymysql params support is limited for identifiers
                sql = f"CREATE USER '{new_user}'@'{host}' IDENTIFIED BY '{new_password}'"
                cursor.execute(sql)
                cursor.execute("FLUSH PRIVILEGES")
            self.conn.commit()
            return True, "Success"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()

    def grant_privileges(self, user, host, database, privileges='ALL PRIVILEGES'):
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                db_part = "*.*" if database == '*' else f"`{database}`.*"
                sql = f"GRANT {privileges} ON {db_part} TO '{user}'@'{host}'"
                cursor.execute(sql)
                cursor.execute("FLUSH PRIVILEGES")
            self.conn.commit()
            return True, "Success"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()

    def drop_user(self, user, host):
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                sql = f"DROP USER '{user}'@'{host}'"
                cursor.execute(sql)
            self.conn.commit()
            return True, "Success"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()

    def get_grants(self, user, host):
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                sql = f"SHOW GRANTS FOR '{user}'@'{host}'"
                cursor.execute(sql)
                # Result key is usually "Grants for user@host"
                return [list(x.values())[0] for x in cursor.fetchall()]
        except Exception as e:
            return [str(e)]
        finally:
            self.close()
