from datetime import datetime

from mcp_workspace_common.extraction.constants import DOCX, PPTX, XLSX

DEMO_NOW = datetime.fromisoformat("2026-11-05T12:00:00-06:00")
GOOGLE_DOC = "application/vnd.google-apps.document"
GOOGLE_SHEET = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDES = "application/vnd.google-apps.presentation"
FOLDER = "application/vnd.google-apps.folder"
EXPORTS = {GOOGLE_DOC: DOCX, GOOGLE_SHEET: XLSX, GOOGLE_SLIDES: PPTX}
GMAIL = "https://www.googleapis.com/auth/gmail."
CAL = "https://www.googleapis.com/auth/calendar."
DRIVE = "https://www.googleapis.com/auth/drive.file"
