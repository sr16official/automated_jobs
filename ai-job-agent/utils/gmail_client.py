import os.path
import base64
import logging
import mimetypes
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

class GmailClient:
    """
    Wrapper for Gmail API to authenticate and create drafts.
    """
    def __init__(self):
        self.logger = logging.getLogger("GmailClient")
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authentication flow with local browser."""
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'token.json')
        creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'credentials.json')

        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    self.logger.error(f"Error refreshing token: {e}")
                    self.creds = None

            if not self.creds:
                if not os.path.exists(creds_path):
                    self.logger.error(f"Credentials file not found at {creds_path}. Please download it from Google Cloud Console.")
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                    with open(token_path, 'w') as token:
                        token.write(self.creds.to_json())
                except Exception as e:
                    self.logger.error(f"Authentication failed: {e}")
                    return

        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
        except HttpError as error:
            self.logger.error(f"An error occurred building Gmail service: {error}")

    def create_draft(self, to_email, subject, body, attachment_path=None):
        """Create a draft email with optional attachment."""
        if not self.service:
            self.logger.error("Gmail service not initialized. Cannot create draft.")
            return None

        try:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = to_email
            message['Subject'] = subject

            if attachment_path and os.path.exists(attachment_path):
                # Guess the content type based on the file's extension.
                content_type, encoding = mimetypes.guess_type(attachment_path)
                if content_type is None or encoding is not None:
                    # No guess could be made, or the file is encoded (compressed), so
                    # use a generic bag-of-bits type.
                    content_type = 'application/octet-stream'
                
                main_type, sub_type = content_type.split('/', 1)
                
                with open(attachment_path, 'rb') as f:
                    file_data = f.read()
                    filename = os.path.basename(attachment_path)
                    
                message.add_attachment(file_data, maintype=main_type, subtype=sub_type, filename=filename)
            elif attachment_path:
                self.logger.warning(f"Attachment not found at {attachment_path}")

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            create_message = {
                'message': {
                    'raw': encoded_message
                }
            }
            
            draft = self.service.users().drafts().create(userId='me', body=create_message).execute()
            
            self.logger.info(f"Draft created. Id: {draft['id']}")
            return draft

        except HttpError as error:
            self.logger.error(f"An error occurred creating draft: {error}")
            return None
