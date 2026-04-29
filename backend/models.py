"""
Pydantic models for Amen! API.

These models define the shape of all data flowing through the API
(request bodies, response payloads, persistent documents).

This module must NOT import from dependencies.py or server.py.
It only depends on the standard library and pydantic.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone


# ==================== USER & AUTH ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    preferred_bible: str = "nuova_diodati"
    language: str = "it"
    country: Optional[str] = None
    bio: Optional[str] = None
    is_public: bool = False
    birth_date: Optional[str] = None  # Format: YYYY-MM-DD
    parental_consent: bool = False  # For minors sharing personal info
    safety_reminder_shown: bool = False  # Track if safety reminder was shown
    # Parental Controls - settings managed by parents
    parental_controls_enabled: bool = False  # Master switch for parental controls
    social_features_enabled: bool = True  # Can use community/chat features
    social_level: str = "friends_only"  # "disabled", "friends_only", "all" (only if adult approved)
    media_sharing_enabled: bool = False  # Can share/receive images/media
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_age(self) -> Optional[int]:
        """Calculate user's age from birth_date"""
        if not self.birth_date:
            return None
        try:
            birth = datetime.strptime(self.birth_date, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return age
        except:
            return None

    def is_minor(self) -> bool:
        """Check if user is under 18"""
        age = self.get_age()
        return age is not None and age < 18


class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionDataResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    session_token: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    language: str = "it"
    country: Optional[str] = None
    birth_date: Optional[str] = None  # Format: YYYY-MM-DD


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str


# ==================== JOURNAL & BOOKMARKS ====================

class JournalEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    mood: str
    language: str = "it"
    ai_insight: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JournalCreate(BaseModel):
    content: str
    mood: str
    language: str = "it"


class Bookmark(BaseModel):
    bookmark_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    book: str
    chapter: int
    verse: int
    text: str
    note: Optional[str] = None
    highlight_color: str = "#D4A574"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BookmarkCreate(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str
    note: Optional[str] = None
    highlight_color: str = "#D4A574"


# ==================== AI CHAT & MOOD ====================

class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    message: str
    mood: Optional[str] = None
    language: str = "it"


class MoodCheckIn(BaseModel):
    checkin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood: str
    verse_reference: str
    verse_text: str
    reflection: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MoodRequest(BaseModel):
    mood: str
    language: str = "it"


# ==================== PROGRESS & DONATIONS ====================

class Progress(BaseModel):
    user_id: str
    reading_streak: int = 0
    total_chapters_read: int = 0
    total_journal_entries: int = 0
    last_reading_date: Optional[datetime] = None
    achievements: List[str] = []


class DonationRequest(BaseModel):
    amount: float
    method: str
    message: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


# ==================== COMMUNITY ====================

class CommunityMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    user_country: Optional[str] = None
    content: str
    original_language: str
    translations: Dict[str, str] = {}
    message_type: str = "text"  # text, audio, prayer_request
    likes: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommunityMessageCreate(BaseModel):
    content: str
    language: str = "it"
    message_type: str = "text"


# ==================== STUDY GROUPS ====================

class StudyGroupMember(BaseModel):
    user_id: str
    user_name: str
    role: str = "member"  # "admin", "member"
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudyGroup(BaseModel):
    group_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_by: str
    members: List[StudyGroupMember] = []
    max_members: int = 30
    current_study: Optional[Dict] = None  # {book, chapter, verse_start, verse_end}
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudyGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class StudyGroupMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    user_id: str
    user_name: str
    content: str
    message_type: str = "chat"  # "chat", "verse_share", "note_share", "study_update"
    shared_content: Optional[Dict] = None  # For verse/note sharing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudyGroupMessageCreate(BaseModel):
    content: str
    message_type: str = "chat"
    shared_content: Optional[Dict] = None


class StudyGroupInvite(BaseModel):
    invite_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    group_name: str
    invited_by: str
    invited_by_name: str
    invited_user_id: str
    status: str = "pending"  # "pending", "accepted", "declined"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_type: str = "text"


# ==================== GROUPS, NOTIFICATIONS, FEELINGS ====================

class FeelingRequest(BaseModel):
    text: str
    language: str = "it"


class BibleGroup(BaseModel):
    group_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    topic: str  # prayer, study, testimony, support, worship
    creator_id: str
    creator_name: str
    members: List[str] = []
    is_public: bool = True
    language: str = "it"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GroupCreate(BaseModel):
    name: str
    description: str
    topic: str
    is_public: bool = True
    language: str = "it"


class GroupPost(BaseModel):
    post_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    user_id: str
    user_name: str
    content: str
    post_type: str = "text"  # text, prayer, verse, testimony
    bible_reference: Optional[str] = None
    likes: int = 0
    comments: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GroupPostCreate(BaseModel):
    content: str
    post_type: str = "text"
    bible_reference: Optional[str] = None


class PostComment(BaseModel):
    comment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PrivateMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    sender_name: str
    receiver_id: str
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PrivateMessageCreate(BaseModel):
    receiver_id: str
    content: str


class Notification(BaseModel):
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    body: str
    notification_type: str  # verse, group, message, like, comment
    data: Dict = {}
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== STUDY NOTES ====================

class StudyNote(BaseModel):
    book: str
    chapter: int
    verse: int
    historical_context: str
    cross_references: List[str]
    hebrew_greek: Optional[str] = None
    application: str
    commentary: str


class StudyNoteCreate(BaseModel):
    book: str
    chapter: int
    verse: Optional[int] = None
    note: str
    highlight_color: Optional[str] = None
    tags: List[str] = []
