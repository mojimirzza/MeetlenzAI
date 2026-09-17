from __future__ import annotations


def can_view_participant_questions(viewer_id: str, owner_id: str, *, is_moderator: bool, strict: bool = True) -> bool:
    if viewer_id == owner_id or is_moderator:
        return True
    return not strict
