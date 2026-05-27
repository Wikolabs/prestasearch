import json
import logging

import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector

from models import Prestataire, SearchResult

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 3072


class PGVectorStore:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @classmethod
    async def create(cls, dsn: str) -> "PGVectorStore":
        # Ensure vector extension exists before pool registers the type codec
        boot = await asyncpg.connect(dsn=dsn)
        try:
            await boot.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        finally:
            await boot.close()
        pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10, init=register_vector)
        store = cls(pool)
        await store._init_schema()
        return store

    async def _init_schema(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS prestataires (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    specialty   TEXT NOT NULL,
                    description TEXT NOT NULL,
                    services    JSONB DEFAULT '[]',
                    city        TEXT DEFAULT '',
                    country     TEXT DEFAULT '',
                    hourly_rate FLOAT DEFAULT 0,
                    phone       TEXT DEFAULT '',
                    email       TEXT DEFAULT '',
                    rating      FLOAT DEFAULT 0,
                    image_base64 TEXT DEFAULT '',
                    created_at  TEXT,
                    embedding   VECTOR({EMBEDDING_DIM})
                );
                CREATE INDEX IF NOT EXISTS idx_presta_emb
                    ON prestataires USING hnsw (embedding vector_cosine_ops);
            """)
        logger.info("PGVectorStore schema ready.")

    @property
    async def count(self) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM prestataires")

    async def add(self, prestataire: Prestataire, embedding: np.ndarray) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO prestataires
                   (id,name,specialty,description,services,city,country,hourly_rate,phone,email,rating,image_base64,created_at,embedding)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14) ON CONFLICT (id) DO NOTHING""",
                prestataire.id, prestataire.name, prestataire.specialty, prestataire.description,
                json.dumps(prestataire.services), prestataire.city, prestataire.country,
                prestataire.hourly_rate, prestataire.phone, prestataire.email,
                prestataire.rating, prestataire.image_base64, prestataire.created_at,
                embedding.tolist(),
            )

    async def update(self, prestataire_id: str, prestataire: Prestataire, embedding: np.ndarray) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE prestataires SET name=$2,specialty=$3,description=$4,services=$5,
                   city=$6,country=$7,hourly_rate=$8,phone=$9,email=$10,rating=$11,
                   image_base64=$12,embedding=$13 WHERE id=$1""",
                prestataire_id, prestataire.name, prestataire.specialty, prestataire.description,
                json.dumps(prestataire.services), prestataire.city, prestataire.country,
                prestataire.hourly_rate, prestataire.phone, prestataire.email,
                prestataire.rating, prestataire.image_base64, embedding.tolist(),
            )
            return result != "UPDATE 0"

    async def list_all(self) -> list[Prestataire]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id,name,specialty,description,services,city,country,hourly_rate,phone,email,rating,image_base64,created_at FROM prestataires ORDER BY created_at DESC"
            )
        return [_row_to_prestataire(r) for r in rows]

    async def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""SELECT id,name,specialty,description,services,city,country,hourly_rate,phone,email,rating,image_base64,created_at,
                           1 - (embedding <=> $1::vector) AS score
                    FROM prestataires
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2""",
                query_embedding.tolist(), top_k,
            )
        return [
            SearchResult(prestataire=_row_to_prestataire(r), similarity_score=max(0.0, min(1.0, float(r["score"]))))
            for r in rows
        ]


def _row_to_prestataire(row) -> Prestataire:
    services = row["services"]
    if isinstance(services, str):
        services = json.loads(services)
    return Prestataire(
        id=row["id"], name=row["name"], specialty=row["specialty"],
        description=row["description"], services=services,
        city=row["city"] or "", country=row["country"] or "",
        hourly_rate=row["hourly_rate"] or 0, phone=row["phone"] or "",
        email=row["email"] or "", rating=row["rating"] or 0,
        image_base64=row["image_base64"] or "", created_at=row["created_at"] or "",
    )
