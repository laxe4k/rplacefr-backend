from pydantic import BaseModel


class Links(BaseModel):
    discord: str = ""
    reddit: str = ""
    tuto: str = ""
    atlas: str = ""
    relations: str = ""


class ConfigResponse(BaseModel):
    event: bool
    links: Links


class Streamer(BaseModel):
    name: str
    profileImage: str
    isLive: bool


class StreamersResponse(BaseModel):
    streamers: list[Streamer]


class HealthResponse(BaseModel):
    status: str
    database: str


# Auth models
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# Admin models
class UpdateEventRequest(BaseModel):
    event: bool


class UpdateLinksRequest(BaseModel):
    discord: str = ""
    reddit: str = ""
    tuto: str = ""
    atlas: str = ""
    relations: str = ""


class AddStreamerRequest(BaseModel):
    name: str


class StreamerListItem(BaseModel):
    name: str


class StreamerListResponse(BaseModel):
    streamers: list[StreamerListItem]
