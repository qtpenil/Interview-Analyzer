from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.core.security import PasswordStr

NAME_PATTERN = r"^[A-Za-z\s'_\-]{2,50}$"


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        validation_alias=AliasChoices("name", "username"),
        min_length=2,
        max_length=50,
        pattern=NAME_PATTERN,
    )
    email: EmailStr
    password: PasswordStr

    @model_validator(mode="before")
    @classmethod
    def strip_name(cls, values: dict) -> dict:
        if isinstance(values, dict) and "name" in values and isinstance(values["name"], str):
            values["name"] = values["name"].strip()
        return values


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SendEmailSchema(BaseModel):
    email: EmailStr


class VerifyEmailSchema(BaseModel):
    email: EmailStr
    otp: str


class ResetPasswordSchema(BaseModel):
    new_password: PasswordStr
    confirm_password: PasswordStr

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class VerifyOTPResponse(BaseModel):
    message: str
    verification_token: str


class UserCheckResponse(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    email: EmailStr
