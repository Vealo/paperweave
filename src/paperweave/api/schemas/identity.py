"""Identity API payloads."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        local, separator, domain = value.partition("@")
        if not separator or not local or "." not in domain or any(char.isspace() for char in value):
            raise ValueError("enter a valid email address")
        return value


class OwnerSetupRequest(CredentialsRequest):
    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("display_name")
    @classmethod
    def trim_display_name(cls, value: str) -> str:
        return value.strip()


class UserCreateRequest(CredentialsRequest):
    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("display_name")
    @classmethod
    def trim_display_name(cls, value: str) -> str:
        return value.strip()


class UserProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    current_password: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("display_name")
    @classmethod
    def trim_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("display name cannot be blank")
        return value

    @field_validator("email")
    @classmethod
    def normalize_profile_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        local, separator, domain = value.partition("@")
        if not separator or not local or "." not in domain or any(char.isspace() for char in value):
            raise ValueError("enter a valid email address")
        return value

    @model_validator(mode="after")
    def require_profile_field(self):
        if self.display_name is None and self.email is None:
            raise ValueError("at least one profile field must be supplied")
        return self


class UserAdminUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    is_active: bool | None = None

    @field_validator("display_name")
    @classmethod
    def trim_admin_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("display name cannot be blank")
        return value

    @field_validator("email")
    @classmethod
    def normalize_admin_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        local, separator, domain = value.partition("@")
        if not separator or not local or "." not in domain or any(char.isspace() for char in value):
            raise ValueError("enter a valid email address")
        return value

    @model_validator(mode="after")
    def require_admin_field(self):
        if self.display_name is None and self.email is None and self.is_active is None:
            raise ValueError("at least one user field must be supplied")
        return self


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class UserSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    theme: Literal["system", "light", "dark"] | None = None

    @model_validator(mode="after")
    def require_setting(self):
        if self.theme is None:
            raise ValueError("at least one setting must be supplied")
        return self


class UserSettingsResponse(BaseModel):
    user_id: str
    theme: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str
    role: str
    avatar_url: str | None = None
    is_active: bool = True


class AuthStatusResponse(BaseModel):
    owner_exists: bool
