MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_EXPANDED_BYTES = 25 * 1024 * 1024
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
SUPPORTED_MIMES = {
    DOCX,
    XLSX,
    PPTX,
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/html",
    "application/json",
}
