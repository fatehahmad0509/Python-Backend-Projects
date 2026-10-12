import requests
import os
from google import genai
import json
from dotenv import load_dotenv
import time
import ssl
import socket
from urllib.parse import urlparse


load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


url = input("🤖 Nova Web Secure 🤖 | Enter site address: ")

if not url.startswith("http://") and not url.startswith("https://"):
    url = "https://" + url


hostname = urlparse(url).hostname

time.sleep(1)
print("Starting Nova Secure Analysis...")

try:
    response = requests.get(url, timeout=10)
except Exception as e:
    print(f"Nova Secure Analysis Error: {e}")
    input("\nPress Enter to Close Terminal")
    exit()

def check_ssl(hostname):
    try:
        context = ssl.create_default_context()

        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        return {
            "valid": "Yes",
            "issuer": dict(x[0] for x in cert["issuer"]).get("organizationName", "Unknown"),
            "expires": cert["notAfter"]
        }

    except Exception:
        return {
            "valid": "No",
            "issuer": "Unknown",
            "expires": "Unknown"
        }

ssl_info = check_ssl(hostname)


def check_cookies(response):
    cookie = response.headers.get("Set-Cookie", "")

    return {
        "secure": "Yes" if "Secure" in cookie else "No",
        "httponly": "Yes" if "HttpOnly" in cookie else "No",
        "samesite": (
            "Lax" if "SameSite=Lax" in cookie else
            "Strict" if "SameSite=Strict" in cookie else
            "None" if "SameSite=None" in cookie else
            "Not Specified"
        )
    }

cookie_info = check_cookies(response)

def analyze_with_ai():
    prompt = f"""You are an AI security agent trained to find and analyze cybersecurity vulnerabilities in websites, and to score website security out of 100 based on provided technical data.
    Your task is to analyze the provided data, evaluate the website's security, give a score out of 100, and determine whether the site is low, medium, or high risk.
    Do not speculate on things you don't know. Base your analysis only on the provided data. The data comes from Python's requests library (e.g. headers.get("Server")).

    Provided data:

    HTTPS Status: {response.url}
    Status Code: {response.status_code}
    Cookie Security:
    Secure: {cookie_info["secure"]}
    HttpOnly: {cookie_info["httponly"]}
    SameSite: {cookie_info["samesite"]}
    Server: {response.headers.get("Server")}
    Strict-Transport-Security: {response.headers.get("Strict-Transport-Security")}
    Content-Security-Policy: {response.headers.get("Content-Security-Policy")}
    X-Frame-Options: {response.headers.get("X-Frame-Options")}
    X-Content-Type-Options: {response.headers.get("X-Content-Type-Options")}
    Permissions-Policy: {response.headers.get("Permissions-Policy")}
    SSL Certificate:
    Valid: {ssl_info["valid"]}
    Issuer: {ssl_info["issuer"]}
    Expires: {ssl_info["expires"]}

    As described, analyze this data, give a score out of 100, and report to the user.

    Use correct technical terms (e.g. write 'HSTS' not 'HTS').
    Set the risk level consistently with the score.
    Base the score only on the provided technical data. Popularity, brand value, or site recognition must not affect the score.
    Briefly explain why each present or missing security header affects the score.

    70-100: Low Risk
    50-69: Medium Risk
    0-49: High Risk

    Only interpret based on the provided data. Do not make definitive judgments about security mechanisms you cannot see. Use phrases like 'likely', 'appears to'.

    Follow these rules strictly.

    NOTE: Return your response as JSON only.

{{
    "score": 0,
    "risk": "",
    "summary": "",
    "strengths": [],
    "weaknesses": [],
    "recommendations": [],
    "reasoning": []
}}

    Write missing security headers in the "weaknesses" field.
    Write present security headers in the "strengths" field.
    Write recommendations in the "recommendations" field.

    Do not write any characters outside of JSON.
    Do not use Markdown.
    Do not create a ```json``` block.
    """

    try:
        ai_response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        text = ai_response.text.strip()

        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        website_analyze_results = json.loads(text)
        return website_analyze_results
    
    except Exception as e:
        print(f"Error {e}")
        return None
    

result = analyze_with_ai()

if result is None:
    print("❌ Analysis Failed, Please Try Again Later")
    input("\nPress Enter to Close Terminal")
    exit()

print(f"⭐ Security Score: {result['score']}/100")
print(f"🚨 Risk: {result['risk']}")
print(f"📝 Summary: {result['summary']}")
print("\n✅ Strengths:")
for item in result.get("strengths", []):
    print(f"- {item}")

print("\n❌ Weaknesses:")
for item in result.get("weaknesses", []):
    print(f"- {item}")

print("\n💡 Recommendations:")
for item in result.get("recommendations", []):
    print(f"- {item}")

print("\n📋 Scoring Reasoning:")
for item in result.get("reasoning", []):
    print(f"- {item}")

input("\nPress Enter to Close Terminal")
