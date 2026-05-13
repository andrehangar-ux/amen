"""
Study Groups endpoints (adults-only).

Provides CRUD for study groups, invitation flow, group messaging,
verse sharing, current passage tracking, and user search for invites.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query

from core import api_router, db
from dependencies import require_auth, is_minor
from models import (
    User,
    StudyGroup,
    StudyGroupCreate,
    StudyGroupMember,
    StudyGroupMessage,
    StudyGroupMessageCreate,
    StudyGroupInvite,
)


@api_router.post("/study-groups")
async def create_study_group(data: StudyGroupCreate, user: User = Depends(require_auth)):
    """Create a new study group (adults only)"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if user_doc and is_minor(user_doc.get("birth_date")):
        raise HTTPException(status_code=403, detail="I minori non possono creare o partecipare ai gruppi di studio")

    group = StudyGroup(
        name=data.name,
        description=data.description,
        created_by=user.user_id,
        members=[StudyGroupMember(user_id=user.user_id, user_name=user.name, role="admin")],
    )

    await db.study_groups.insert_one(group.dict())

    return {
        "success": True,
        "group_id": group.group_id,
        "name": group.name,
        "message": "Gruppo di studio creato",
    }


@api_router.get("/study-groups")
async def get_my_study_groups(user: User = Depends(require_auth)):
    """Get all study groups the user is a member of"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if user_doc and is_minor(user_doc.get("birth_date")):
        raise HTTPException(status_code=403, detail="I minori non possono accedere ai gruppi di studio")

    groups = await db.study_groups.find(
        {"members.user_id": user.user_id, "is_active": True},
        {"_id": 0},
    ).to_list(100)

    return {"groups": groups}


@api_router.get("/study-groups/search-users")
async def search_users_for_invite(
    q: str = Query(..., min_length=2),
    user: User = Depends(require_auth),
):
    """Search for users to invite to a study group.

    NOTE: Declared BEFORE /study-groups/{group_id} so the literal path
    "search-users" is not captured as a {group_id} path parameter.
    """
    users = await db.users.find(
        {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
            ],
            "user_id": {"$ne": user.user_id},  # Exclude self
        },
        {"_id": 0, "user_id": 1, "name": 1, "email": 1, "birth_date": 1},
    ).limit(20).to_list(20)

    adult_users = [
        {"user_id": u["user_id"], "name": u["name"], "email": u.get("email", "")}
        for u in users
        if not is_minor(u.get("birth_date"))
    ]

    return {"users": adult_users}


@api_router.get("/study-groups/{group_id}")
async def get_study_group(group_id: str, user: User = Depends(require_auth)):
    """Get a specific study group"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if user_doc and is_minor(user_doc.get("birth_date")):
        raise HTTPException(status_code=403, detail="I minori non possono accedere ai gruppi di studio")

    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )

    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    return group


@api_router.post("/study-groups/{group_id}/invite")
async def invite_to_study_group(
    group_id: str,
    invited_user_id: str = Query(...),
    user: User = Depends(require_auth),
):
    """Invite a user to join the study group (any member can invite)"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if user_doc and is_minor(user_doc.get("birth_date")):
        raise HTTPException(status_code=403, detail="I minori non possono accedere ai gruppi di studio")

    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )
    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    invited_user = await db.users.find_one({"user_id": invited_user_id}, {"_id": 0})
    if not invited_user:
        raise HTTPException(status_code=404, detail="Utente invitato non trovato")
    if is_minor(invited_user.get("birth_date")):
        raise HTTPException(status_code=403, detail="Non puoi invitare utenti minorenni")

    if any(m["user_id"] == invited_user_id for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="L'utente è già membro del gruppo")

    if len(group.get("members", [])) >= group.get("max_members", 30):
        raise HTTPException(status_code=400, detail="Il gruppo ha raggiunto il numero massimo di membri")

    existing_invite = await db.study_group_invites.find_one({
        "group_id": group_id,
        "invited_user_id": invited_user_id,
        "status": "pending",
    })
    if existing_invite:
        raise HTTPException(status_code=400, detail="Esiste già un invito pendente per questo utente")

    invite = StudyGroupInvite(
        group_id=group_id,
        group_name=group["name"],
        invited_by=user.user_id,
        invited_by_name=user.name,
        invited_user_id=invited_user_id,
    )

    await db.study_group_invites.insert_one(invite.dict())

    return {"success": True, "invite_id": invite.invite_id, "message": "Invito inviato"}


@api_router.get("/study-groups/invites/pending")
async def get_pending_invites(user: User = Depends(require_auth)):
    """Get all pending invites for the current user"""
    invites = await db.study_group_invites.find(
        {"invited_user_id": user.user_id, "status": "pending"},
        {"_id": 0},
    ).to_list(50)

    return {"invites": invites}


@api_router.post("/study-groups/invites/{invite_id}/respond")
async def respond_to_invite(
    invite_id: str,
    accept: bool = Query(...),
    user: User = Depends(require_auth),
):
    """Accept or decline a study group invite"""
    invite = await db.study_group_invites.find_one(
        {"invite_id": invite_id, "invited_user_id": user.user_id, "status": "pending"},
        {"_id": 0},
    )

    if not invite:
        raise HTTPException(status_code=404, detail="Invito non trovato")

    if accept:
        group = await db.study_groups.find_one({"group_id": invite["group_id"]})
        if not group:
            raise HTTPException(status_code=404, detail="Gruppo non trovato")

        if len(group.get("members", [])) >= group.get("max_members", 30):
            raise HTTPException(status_code=400, detail="Il gruppo è pieno")

        new_member = StudyGroupMember(user_id=user.user_id, user_name=user.name)
        await db.study_groups.update_one(
            {"group_id": invite["group_id"]},
            {"$push": {"members": new_member.dict()}},
        )

        await db.study_group_invites.update_one(
            {"invite_id": invite_id},
            {"$set": {"status": "accepted"}},
        )

        return {"success": True, "message": "Sei entrato nel gruppo", "group_id": invite["group_id"]}
    else:
        await db.study_group_invites.update_one(
            {"invite_id": invite_id},
            {"$set": {"status": "declined"}},
        )
        return {"success": True, "message": "Invito rifiutato"}


@api_router.post("/study-groups/{group_id}/leave")
async def leave_study_group(group_id: str, user: User = Depends(require_auth)):
    """Leave a study group"""
    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )

    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    await db.study_groups.update_one(
        {"group_id": group_id},
        {"$pull": {"members": {"user_id": user.user_id}}},
    )

    updated_group = await db.study_groups.find_one({"group_id": group_id})
    if not updated_group.get("members"):
        await db.study_groups.update_one(
            {"group_id": group_id},
            {"$set": {"is_active": False}},
        )

    return {"success": True, "message": "Hai lasciato il gruppo"}


@api_router.post("/study-groups/{group_id}/messages")
async def send_group_message(
    group_id: str,
    data: StudyGroupMessageCreate,
    user: User = Depends(require_auth),
):
    """Send a message to the study group"""
    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )
    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    message = StudyGroupMessage(
        group_id=group_id,
        user_id=user.user_id,
        user_name=user.name,
        content=data.content,
        message_type=data.message_type,
        shared_content=data.shared_content,
    )

    await db.study_group_messages.insert_one(message.dict())

    return {"success": True, "message_id": message.message_id}


@api_router.get("/study-groups/{group_id}/messages")
async def get_group_messages(
    group_id: str,
    limit: int = 50,
    before: Optional[str] = None,
    user: User = Depends(require_auth),
):
    """Get messages from the study group"""
    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )
    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    query = {"group_id": group_id}
    if before:
        query["message_id"] = {"$lt": before}

    messages = await db.study_group_messages.find(
        query,
        {"_id": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return {"messages": list(reversed(messages))}


@api_router.put("/study-groups/{group_id}/study")
async def update_current_study(
    group_id: str,
    book: str = Query(...),
    chapter: int = Query(...),
    verse_start: int = Query(1),
    verse_end: int = Query(None),
    user: User = Depends(require_auth),
):
    """Update the current study passage for the group (any member can update)"""
    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )
    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    current_study = {
        "book": book,
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "updated_by": user.user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.study_groups.update_one(
        {"group_id": group_id},
        {"$set": {"current_study": current_study}},
    )

    system_message = StudyGroupMessage(
        group_id=group_id,
        user_id=user.user_id,
        user_name=user.name,
        content=f"Ha aggiornato lo studio corrente: {book} {chapter}:{verse_start}" + (f"-{verse_end}" if verse_end else ""),
        message_type="study_update",
        shared_content=current_study,
    )
    await db.study_group_messages.insert_one(system_message.dict())

    return {"success": True, "current_study": current_study}


@api_router.post("/study-groups/{group_id}/share-verse")
async def share_verse_to_group(
    group_id: str,
    book: str = Query(...),
    chapter: int = Query(...),
    verse: int = Query(...),
    text: str = Query(...),
    note: Optional[str] = None,
    user: User = Depends(require_auth),
):
    """Share a verse with the study group"""
    group = await db.study_groups.find_one(
        {"group_id": group_id, "members.user_id": user.user_id},
        {"_id": 0},
    )
    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato o non sei membro")

    shared_content = {
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "text": text,
        "note": note,
    }

    message = StudyGroupMessage(
        group_id=group_id,
        user_id=user.user_id,
        user_name=user.name,
        content=f"{book} {chapter}:{verse}",
        message_type="verse_share",
        shared_content=shared_content,
    )

    await db.study_group_messages.insert_one(message.dict())

    return {"success": True, "message_id": message.message_id}
