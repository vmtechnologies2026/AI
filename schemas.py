from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: str
    password: str

class ChatCreateIn(BaseModel):
    title: str = Field(default="New conversation", max_length=200)

class ChatIn(BaseModel):
    chat_id: int | None = None
    message: str = Field(min_length=1, max_length=12000)
    mode: str = Field(default="chat", pattern="^(chat|code)$")
