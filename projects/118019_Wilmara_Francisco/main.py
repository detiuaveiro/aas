import imaplib
import email
import time
from naive_bayes import bayes, train_algorithm


def get_email_credentials():
    email_address = input("Enter your email address: ")
    email_password = input("Enter your email password: ")
    imap_server = input("Enter your IMAP server address (e.g., imap.yourprovider.com): ")
    return email_address, email_password, imap_server


def test_spam_classifier_bayes(text):
    print(f"The text: '{text}'")
    probability = bayes(text)
    if probability > 0.5:
        print(f"The text '{text}' is classified as SPAM with a probability of {probability:.4f}")
    else:
        print(f"The text '{text}' is classified as HAM with a probability of {1 - probability:.4f}")


def is_suspicious_email(msg):
    # Extract relevant information from the email headers
    sender = msg["From"]
    subject = msg["Subject"]

    test_spam_classifier_bayes(subject.lower())

    # Check for suspicious patterns based on security policies
    if "unsub" in subject.lower() or "unsubscribe" in subject.lower():
        return True

    if "urgent" in subject.lower():
        return True

    if "verify your account" in subject.lower():
        return True

    # Check if the sender is a known phishing domain
    known_phishing_domains = ["att-rsshelp.com", "paypal-opladen.be", "login.microsoftonline.ccisystems.us",
                              "dhlinfos.link", "facebookztv.com", "login-amazon-account.com"]
    sender_domain = sender.split('@')[-1].lower()
    if sender_domain in known_phishing_domains:
        return True

    # Check if the sender's email address is similar to a trusted domain
    trusted_domains = ["ua.pt", "gmail.com", "outlook.com"]
    if not any(trusted_domain in sender.lower() for trusted_domain in trusted_domains):
        return True

    # Check for mismatch between the displayed sender name and the actual email address
    if sender != msg.get("Reply-To", sender):
        return True

    return False


def check_for_new_emails(imap):
    while True:
        try:
            status, messages = imap.select("inbox", readonly=True)
            if status == 'OK':
                _, msg_ids = imap.search(None, 'UNSEEN')

                for msg_id in msg_ids[0].split():
                    _, msg_data = imap.fetch(msg_id, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract and process email data here
                    print("New email received:")
                    print("Subject:", msg["Subject"])
                    print("From:", msg["From"])
                    print("Body:", msg.get_payload())

                    # Check if the email is suspicious
                    if is_suspicious_email(msg):
                        print("This email appears to be suspicious!")

                time.sleep(60)  # Check for new emails every 60 seconds

        except Exception as e:
            print("Error:", e)
            break


def main():
    print("Start trainning Naive Bayes for email classification...")
    train_algorithm()
    print("End trainning Naive Bayes for email classification...")

    email_address, email_password, imap_server = get_email_credentials()

    try:
        imap = imaplib.IMAP4(imap_server)
        imap.starttls()
        imap.login(email_address, email_password)
        imap.select("inbox")

        print("Connected to email account. Waiting for new emails...")

        check_for_new_emails(imap)

    except Exception as e:
        print("Error:", e)

    finally:
        try:
            imap.close()
            imap.logout()
        except:
            pass


if __name__ == "__main__":
    main()
