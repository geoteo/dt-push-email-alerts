import imaplib
import email
import json
import requests
from py_console import console, bgColor, textColor

# Email/Passwords/API Key
from secrets import secrets

def mailConnect():
    # Connect and login to IMAP mail server
    username = secrets.get('EMAIL')
    password = secrets.get('PASSWORD')
    mail_server = "imap.gmail.com"
    imap_server = imaplib.IMAP4_SSL(host=mail_server)
    imap_server.login(username, password)

    # Choose the mailbox (folder) to search (Case sensitive!)
    imap_server.select("INBOX")  # Default is `INBOX`

    # Search for emails in the mailbox that was selected.
    # First, you need to search and get the message IDs.
    # Then you can fetch specific messages with the IDs.
    # Search filters are explained in the RFC at:
    # https://tools.ietf.org/html/rfc3501#section-6.4.4
    search_criteria = "UnSeen"
    charset = None  # All
    respose_code, message_numbers_raw = imap_server.search(charset, search_criteria)
    console.success(f"Gmail IMAP search response: {respose_code}")  # e.g. OK
    message_numbers = message_numbers_raw[0].split()

    # Fetch full message based on the message numbers obtained from search
    for message_number in message_numbers:
        _, msg = imap_server.fetch(message_number, "(RFC822)")
        # print(f"Fetch response for message {message_number}: {response_code}")
        # print(f"Raw email data:\n{msg[0][1]}")

        # Parse the raw email message in to a convenient object
        message = email.message_from_bytes(msg[0][1])

        console.info(f'From: {message["from"]}')
        console.info(f'To: {message["to"]}')
        console.info(f'Subject: {message["subject"]}')
        console.info(f'Date: {message["date"]}')

        for part in message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                console.info(f'Body: {body.decode("UTF-8")}')
                body = f'{body.decode("UTF-8")}'

        pushAlert(message["date"], message["from"], message["subject"], body)

    imap_server.close()
    imap_server.logout()


def pushAlert(date, who, sub, body):

    tenant = secrets.get('TENANT')
    url = "/api/v2/events/ingest"
    key = secrets.get('KEY')

    req_url = f"{tenant}{url}?Api-Token={key}"
    payload = {
        "eventType": "CUSTOM_ALERT",
        "title": sub,
        "properties": {"From": who, "Date": date, "Subject": sub, "Body": body},
    }

    console.success(f"DYNATRACE REQUEST URL: {req_url}")


    console.success(
        console.highlight(
            json.dumps(payload, indent=2),
            textColor=textColor.YELLOW,
            bgColor=bgColor.BLACK,
        ),
        showTime=False,
    )

    newHeaders = {"Content-type": "application/json", "charset": "utf-8"}
    response = requests.post(req_url, json.dumps(payload), headers=newHeaders)

    console.success("DYNATRACE API RESPONSE:")
    jresponse = response.json()

    console.success(
        console.highlight(
            json.dumps(jresponse, indent=2),
            textColor=textColor.YELLOW,
            bgColor=bgColor.BLACK,
        ),
        showTime=False,
    )


mailConnect()
