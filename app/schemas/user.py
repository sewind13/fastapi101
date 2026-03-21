from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72, examples=["secret1234"])

class UserPublic(UserBase):
    id: int
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)