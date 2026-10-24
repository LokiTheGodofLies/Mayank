from datetime import datetime
from database.connection import db

BAN_TYPES = {"user", "group", "channel"}


async def init_ban_indexes() -> None:
    if db is None:
        return

    collection = db["ban_logs"]
    await collection.create_index("entity_type")
    await collection.create_index("entity_id")
    await collection.create_index("status")
    await collection.create_index([("entity_type", 1), ("entity_id", 1)], unique=True)


async def get_ban_record(entity_type: str, entity_id: int | str) -> dict | None:
    if db is None:
        return None

    return await db["ban_logs"].find_one({
        "entity_type": str(entity_type).lower(),
        "entity_id": str(entity_id),
    })


async def is_entity_banned(entity_type: str, entity_id: int | str) -> bool:
    record = await get_ban_record(entity_type, entity_id)
    return bool(record and record.get("status") == "banned")


async def ban_entity(
    entity_type: str,
    entity_id: int | str,
    reason: str | None = None,
    banned_by: str | None = None,
) -> dict:
    if db is None:
        return {"status": "db_unavailable"}

    entity_type = str(entity_type).lower()
    if entity_type not in BAN_TYPES:
        return {"status": "invalid_type"}

    entity_id = str(entity_id)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    existing = await get_ban_record(entity_type, entity_id)
    if existing and existing.get("status") == "banned":
        if reason and str(reason).strip():
            await db["ban_logs"].update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "reason": str(reason).strip(),
                    "updated_at": now,
                    "banned_by": banned_by or existing.get("banned_by"),
                }},
            )
            return {"status": "updated", "record": existing}

        return {"status": "already_banned", "record": existing}

    final_reason = str(reason or "Reason not stated").strip() or "Reason not stated"

    await db["ban_logs"].update_one(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"$set": {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "reason": final_reason,
            "status": "banned",
            "banned_by": banned_by or "admin",
            "created_at": now,
            "updated_at": now,
        }},
        upsert=True,
    )

    return {"status": "banned", "record": await get_ban_record(entity_type, entity_id)}
