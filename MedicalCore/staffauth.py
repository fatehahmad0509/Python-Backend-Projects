from database import get_connection

class StaffAuth:
    def create_appointment(
        self, full_name, phone, gender, blood_type,
        id_no, birth_date, doctor_id, app_date, app_time
    ):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            query = """
            INSERT INTO appointments(
                full_name, phone, gender, blood_type,
                id_no, birth_date, doctor_id, date, time
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                full_name, phone, gender, blood_type,
                id_no, birth_date, doctor_id, app_date, app_time
            ))

            connection.commit()
            return True
        except:
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()

    def add_doctor(self, doctor_id, full_name, id_no, birthdate):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            query = """
            INSERT INTO doctors(doctor_id, full_name, id_no, birthdate)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (doctor_id, full_name, id_no, birthdate))
            connection.commit()
            return True
        except:
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()

    def delete_doctor(self, doctor_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM doctors WHERE doctor_id = %s;", (doctor_id,))
            connection.commit()
            return True
        except:
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()

    def list_doctors(self):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM doctors ORDER BY full_name ASC")
            return cursor.fetchall()
        except:
            return []
        finally:
            cursor.close()
            connection.close()