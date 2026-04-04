
from pydantic import BaseModel, ConfigDict, EmailStr, Field

USER_ROLES = {"user", "ops_admin", "platform_admin"}


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, examples=["secret1234"])
    phone: str | None = None

class UserPublic(UserBase):
    id: int
    is_active: bool = True
    email_verified: bool = False
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)
