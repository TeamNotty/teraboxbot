from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

mongo = AsyncIOMotorClient(MONGO_URL)

db = mongo.TeraBot
usersdb = db.users
premiumdb = db.premium
settingsdb = db.settings


# ---------------- USERS ---------------- #

async def is_served_user(user_id: int) -> bool:
    user = await usersdb.find_one({"user_id": user_id})
    return bool(user)


async def add_served_user(user_id: int):
    if await is_served_user(user_id):
        return
    return await usersdb.insert_one(
        {"user_id": user_id, "used_today": 0}
    )


async def reset_daily():
    await usersdb.update_many({}, {"$set": {"used_today": 0}})


# ---------------- PREMIUM ---------------- #

async def is_premium(user_id: int) -> bool:
    user = await premiumdb.find_one({"user_id": user_id})
    return bool(user)


async def add_premium(user_id: int):
    return await premiumdb.insert_one({"user_id": user_id})


# ---------------- SETTINGS ---------------- #

async def get_daily_limit():
    data = await settingsdb.find_one({"type": "limits"})
    if not data:
        await settingsdb.insert_one(
            {"type": "limits", "normal": 10, "premium": 50}
        )
        return 10, 50
    return data["normal"], data["premium"]


async def set_daily_limit(normal: int, premium: int):
    return await settingsdb.update_one(
        {"type": "limits"},
        {"$set": {"normal": normal, "premium": premium}},
        upsert=True
    )


# ---------------- USAGE CHECK ---------------- #

async def can_download(user_id: int) -> bool:
    await add_served_user(user_id)

    normal_limit, premium_limit = await get_daily_limit()

    user = await usersdb.find_one({"user_id": user_id})
    used = user.get("used_today", 0)

    if await is_premium(user_id):
        return used < premium_limit
    else:
        return used < normal_limit


async def increase_usage(user_id: int):
    return await usersdb.update_one(
        {"user_id": user_id},
        {"$inc": {"used_today": 1}}
    )
