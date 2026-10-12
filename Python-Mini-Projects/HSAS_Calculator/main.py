import time

student_name = input("Welcome to the High School Achievement Score (OBP) Calculator! Please enter the student's full name: ")
first_written_grade = int(input("Enter " + student_name + "'s first written exam grade: "))
second_written_grade = int(input("Enter the second written exam grade: "))
first_oral_grade = int(input("Enter the first oral exam grade: "))
second_oral_grade = int(input("Enter the second oral exam grade: "))

total_points = first_written_grade + second_written_grade + first_oral_grade + second_oral_grade
HSAS = total_points / 4

result = student_name + "'s High School Achievement Score (HSAS) = " + str(HSAS)
print(result)

time.sleep(10)