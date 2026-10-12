# ✈️ NF Air - Flight Booking & Check-in System

This is a Python-based flight management simulation that allows users to search for routes, book tickets with dynamic pricing, and perform an automated check-in with email notifications.

## 🚀 Features
- **Dynamic Flight Generation:** Generates random flight numbers and departure/arrival times using Python's `datetime` and `timedelta` modules.
- **Smart Pricing:** Calculates ticket costs based on passenger type (Adult/Child) and extra baggage weight.
- **Seat Management:** Real-time seat availability tracking and reservation.
- **Automated Emailing:** Sends professional booking confirmations and boarding passes using `smtplib` and `EmailMessage`.
- **Security First:** Sensitive credentials (like App Passwords) are managed via environment variables to ensure system security.


## 🛡️ Security Note
This project demonstrates the use of **Environment Variables** for handling sensitive information. Hardcoding passwords is avoided to follow industry-standard security practices (Best Practices).

Installation

Open a .env file and write the following into it:

MAIL_USER=youremailaddress
MAIL_PASS=yourapppassword
