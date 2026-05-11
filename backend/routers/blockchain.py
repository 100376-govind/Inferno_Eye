# backend/routers/blockchain.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import BlockOut
from backend.services import blockchain_service

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])


@router.get("/log")
async def get_blockchain(db: AsyncSession = Depends(get_db)):
    blocks = await blockchain_service.get_all_blocks(db)
    return [BlockOut.model_validate(b) for b in blocks]


@router.get("/validate")
async def validate(db: AsyncSession = Depends(get_db)):
    return await blockchain_service.validate_chain(db)
