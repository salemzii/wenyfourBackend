from fastapi import HTTPException, status

contactus_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="unable to create contact us object"
)


support_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="unable to create support object"
)