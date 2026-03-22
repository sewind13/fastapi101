from fastapi import HTTPException, status

class UserNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="ไม่พบข้อมูลผู้ใช้งานในระบบ"
        )

class ItemNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="ไม่พบไอเทมที่คุณต้องการ"
        )