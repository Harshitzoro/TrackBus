
"""Schemas for student notification registration."""

from pydantic import BaseModel, Field


class NotificationRegistrationRequest(BaseModel):
    fcm_token: str = Field(min_length=20, max_length=4096)


class NotificationRegistrationResponse(BaseModel):
    status: str
    message: str
