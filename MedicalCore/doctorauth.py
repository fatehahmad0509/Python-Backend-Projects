from database import get_connection

class DoctorAuth:
    def list_appointments(self, doctor_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            query = """
            SELECT 
                full_name,
                appointment_id,
                birth_date,
                date,
                time,
                status
            FROM appointments
            WHERE doctor_id = %s
            ORDER BY date, time;
            """
            cursor.execute(query, (doctor_id,))
            return cursor.fetchall()
        except:
            return []
        finally:
            cursor.close()
            connection.close()

    def get_patient_profile(self, appointment_id):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT * FROM appointments WHERE appointment_id = %s",
                (appointment_id,)
            )
            return cursor.fetchone()
        except:
            return None
        finally:
            cursor.close()
            connection.close()

    def add_diagnosis(self, appointment_id, diagnosis):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            query = """
            UPDATE appointments 
            SET 
                medical_history = COALESCE(medical_history, '') || '\n- ' || %s,
                status = 'completed'
            WHERE appointment_id = %s
            """
            cursor.execute(query, (diagnosis, appointment_id))

            connection.commit()
            return True
        except:
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()