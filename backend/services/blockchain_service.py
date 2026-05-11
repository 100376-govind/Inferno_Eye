# backend/services/blockchain_service.py
import hashlib
import json
import time
import asyncio
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import BlockchainBlock


DIFFICULTY = 2  # hash must start with '00'


def _calculate_hash(index: int, timestamp: float, event_type: str,
                    data: dict, prev_hash: str, nonce: int) -> str:
    content = f"{index}{timestamp}{event_type}{json.dumps(data, sort_keys=True)}{prev_hash}{nonce}"
    return hashlib.sha256(content.encode()).hexdigest()


def _mine_block(index: int, timestamp: float, event_type: str,
                data: dict, prev_hash: str) -> tuple[str, int]:
    nonce = 0
    prefix = "0" * DIFFICULTY
    while True:
        h = _calculate_hash(index, timestamp, event_type, data, prev_hash, nonce)
        if h.startswith(prefix):
            return h, nonce
        nonce += 1


async def add_block(db: AsyncSession, event_type: str, data: dict) -> BlockchainBlock:
    """Mine a new block and persist it."""
    # Get last block
    result = await db.execute(
        select(BlockchainBlock).order_by(BlockchainBlock.index.desc()).limit(1)
    )
    last = result.scalar_one_or_none()

    index    = (last.index + 1) if last else 0
    prev_hash = last.block_hash if last else "0" * 64
    ts        = time.time()

    # Mine in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    block_hash, nonce = await loop.run_in_executor(
        None, _mine_block, index, ts, event_type, data, prev_hash
    )

    block = BlockchainBlock(
        index=index,
        event_type=event_type,
        data=data,
        prev_hash=prev_hash,
        block_hash=block_hash,
        nonce=nonce,
        timestamp=ts,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def get_all_blocks(db: AsyncSession) -> List[BlockchainBlock]:
    result = await db.execute(
        select(BlockchainBlock).order_by(BlockchainBlock.index.asc())
    )
    return list(result.scalars().all())


async def validate_chain(db: AsyncSession) -> dict:
    blocks = await get_all_blocks(db)
    if not blocks:
        return {"valid": True, "chain_length": 0, "message": "Empty chain"}

    prefix = "0" * DIFFICULTY
    for i, block in enumerate(blocks):
        expected = _calculate_hash(
            block.index, block.timestamp, block.event_type,
            block.data, block.prev_hash, block.nonce
        )
        if expected != block.block_hash:
            return {"valid": False, "chain_length": len(blocks),
                    "message": f"Block {block.index} hash mismatch"}
        if not block.block_hash.startswith(prefix):
            return {"valid": False, "chain_length": len(blocks),
                    "message": f"Block {block.index} fails proof-of-work"}
        if i > 0 and block.prev_hash != blocks[i - 1].block_hash:
            return {"valid": False, "chain_length": len(blocks),
                    "message": f"Block {block.index} broken chain link"}

    return {"valid": True, "chain_length": len(blocks), "message": "Chain integrity verified ✓"}
