import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from assistant.utils.logger import setup_logger

logger = setup_logger()


def _get_credentials():
    from assistant.utils.config import EMAIL_ADDRESS, EMAIL_PASSWORD
    return EMAIL_ADDRESS, EMAIL_PASSWORD


def send(to: str, subject: str, body: str) -> str:
    addr, pwd = _get_credentials()
    if not addr or not pwd:
        return "Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"
    try:
        msg = MIMEMultipart()
        msg['From'] = addr
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(addr, pwd)
            server.send_message(msg)
        return f"Email sent to {to}"
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return f"Failed to send email: {e}"


def inbox(count: int = 5) -> str:
    addr, pwd = _get_credentials()
    if not addr or not pwd:
        return "Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(addr, pwd)
        mail.select('inbox')
        _, data = mail.search(None, 'UNSEEN')
        ids = data[0].split()
        if not ids:
            mail.logout()
            return "No unread emails."
        ids = ids[-count:]
        lines = [f"{len(ids)} unread email(s):\n"]
        for eid in reversed(ids):
            _, msg_data = mail.fetch(eid, '(RFC822)')
            msg = email_lib.message_from_bytes(msg_data[0][1])
            lines.append(f"From:    {msg['From']}")
            lines.append(f"Subject: {msg['Subject']}\n")
        mail.logout()
        return '\n'.join(lines).strip()
    except Exception as e:
        logger.error(f"Inbox error: {e}")
        return f"Failed to check inbox: {e}"


def handle(args: str) -> str:
    """
    Dispatch:
      inbox            — list unread
      send <to> <subject> <body>
    """
    parts = args.strip().split(None, 3)
    if not parts:
        return "Usage:\n  /inbox\n  /send <to> <subject> <body>"
    cmd = parts[0].lower()
    if cmd == 'inbox':
        return inbox()
    if cmd == 'send':
        if len(parts) < 4:
            return "Usage: /send <to> <subject> <body>"
        return send(parts[1], parts[2], parts[3])
    return "Usage:\n  /inbox\n  /send <to> <subject> <body>"
