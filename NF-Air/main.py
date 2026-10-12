import random
from email.message import EmailMessage
import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_ADDRESS = os.getenv("MAIL_USER")
EMAIL_PASSWORD = os.getenv("MAIL_PASS")
adultpassengercount = 0
childpassengercount = 0
flightinformations = {}

passportnumber = ""
totalpayment = 0

gatenumber = random.randint(10, 99)
gateterminal = random.choice("ABCDF")
gate = gateterminal + str(gatenumber)


def checkinemail(to_email, flightnumber, fullname, flightdestination, departurehour, arrivehour, seat, gender,
                 emailadress, gate, passportnumber):
    msg = EmailMessage()
    msg['Subject'] = "Boarding Pass | Flight " + flightnumber
    msg['From'] = "welcome.nfbank@gmail.com"
    msg['To'] = to_email
    msg.set_content(f"""Thank you for purchasing your ticket from NF Air! Here Is Your Boarding Pass:

--------BOARDING PASS--------
Flight Number: {flightnumber}
Full Name: {fullname}
Destination: {flightdestination}
Departure Time: {departurehour}
Arrival Time: {arrivehour}
Seat: {seat}
Gender: {gender}
Email Address: {emailadress}
Gate: {gate}
Passport Number: {passportnumber}
_____________________________


Thanks For Travelling With NF Air!""")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def send_welcome_email(to_email, flightnumber, flightdestination, departurehour, arrivehour, seat, payment,
                       baggageweight):
    msg = EmailMessage()
    msg['Subject'] = "Flight " + flightnumber
    msg['From'] = "welcome.nfbank@gmail.com"
    msg['To'] = to_email
    msg.set_content(f"""Thank you for purchasing your ticket from NF Air! Here Are Your Flight Informations:

Flight Number: {flightnumber}
Destination: {flightdestination}
Departure Time: {departurehour}
Arrival Time: {arrivehour}
Seat: {seat}
Net Baggage Weight: {baggageweight} KG
Payment: {payment} EUR

Thanks For Travelling With NF Air! Please Check In Shortly""")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


numbers = random.randint(1234567, 9999999)
flightnumber = "NF" + str(numbers)
availableseats = ["1A", "2A", "3A", "4A", "5A", "6A", "7A", "8A", "9A", "10A", "1B", "2B", "3B", "4B", "5B", "6B", "7B",
                  "8B", "9B", "10B", "1C", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "1D", "2D", "3D",
                  "4D", "5D", "6D", "7D", "8D", "9D", "10D", ]


def checkin(passengers):
    for p in passengers:
        flightnumber = p["flightnumber"]
        destination = p["destination"]
        departurehour = p["departurehour"]
        arrivalhour = p["arrivalhour"]
        fullname = p["fullname"]
        dateofbirth = p["dateofbirth"]
        age = p["age"]
        passportnumber = p["passportnumber"]
        seat = p["seat"]
        gender = p["gender"]
        emailadress = p["emailadress"]
        checkinemail(emailadress, flightnumber, fullname, destination, departurehour, arrivalhour, seat, gender,
                     emailadress, gate, passportnumber)

    return "Check In Successful!"


def enterroute(departure, arrival):
    destination = departure + " - " + arrival
    return destination


def flightinfos(destination, flightnumber):
    from datetime import datetime, timedelta
    now = datetime.now()
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    departure_dt = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
    arrival_dt = departure_dt + timedelta(hours=3)
    departurehour = departure_dt.strftime("%H:%M")
    arrivalhour = arrival_dt.strftime("%H:%M")
    return {
        "destination": destination,
        "flightnumber": flightnumber,
        "departurehour": departurehour,
        "arrivalhour": arrivalhour,
    }


def buyticket(passengers, baggageweight, checkinwanted, destination, departurehour, arrivalhour):
    """
    passengers: list of dicts, her dict:
        {
            "fullname": str,
            "gender": str,
            "passportnumber": str,
            "emailadress": str,
            "seat": str
        }
    baggageweight: int
    checkinwanted: bool
    """
    global availableseats, totalpayment
    totalpayment = 0
    totalpayment += len([p for p in passengers if p.get("adult", True)]) * 300
    totalpayment += len([p for p in passengers if not p.get("adult", True)]) * 200

    for p in passengers:
        seat = p["seat"]
        if seat in availableseats:
            availableseats.remove(seat)
        else:
            return f"Seat {seat} is not available"

    if baggageweight > 3:
        totalpayment += (baggageweight - 3) * 5

    for p in passengers:
        send_welcome_email(
            p["emailadress"],
            flightnumber,
            destination,
            departurehour,
            arrivalhour,
            p["seat"],
            totalpayment,
            baggageweight
        )

    if checkinwanted:
        checkin()
        return {
            "message": "Payment successful, proceed to check-in",
            "total": totalpayment,
            "seats": [p["seat"] for p in passengers]
        }
    else:
        return {
            "message": "Payment successful",
            "total": totalpayment,
            "seats": [p["seat"] for p in passengers]
        }


if __name__ == "__main__":
    from gui import NFAirApp

    app = NFAirApp()
    app.mainloop()