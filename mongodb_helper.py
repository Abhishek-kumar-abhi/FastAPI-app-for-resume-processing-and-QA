import motor.motor_asyncio
from bson.objectid import ObjectId

class MongoDBClient:
    def __init__(self, uri: str, db_name: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.col = self.db["candidates"]

    async def insert_candidate(self, doc: dict):
        res = await self.col.insert_one(doc)
        return res.inserted_id

    async def list_candidates_summary(self):
        cursor = self.col.find({}, {"candidate_id": 1, "introduction": 1, "skills": 1, "created_at": 1})
        items = []
        async for d in cursor:
            d["_id"] = str(d["_id"])
            items.append(d)
        return items

    async def get_candidate_by_id(self, candidate_id: str):
        # Try matching candidate_id (supabase metadata id), else try Mongo _id
        doc = await self.col.find_one({"candidate_id": candidate_id})
        if not doc:
            try:
                doc = await self.col.find_one({"_id": ObjectId(candidate_id)})
            except Exception:
                doc = None
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
