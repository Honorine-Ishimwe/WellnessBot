"""
Cleanup job: Delete conversations older than 30 days.
Run as a Render Cron Job: python cleanup_job.py
Schedule: 0 3 * * * (daily at 3 AM UTC)
"""

import os
from dotenv import load_dotenv

load_dotenv()

from db import query, execute, close_pool
from logger import logger


RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))


def cleanup_old_conversations():
    """Delete conversations older than RETENTION_DAYS."""
    result = query(
        """
        DELETE FROM conversations
        WHERE updated_at < NOW() - INTERVAL '%s days'
        RETURNING id
        """,
        (RETENTION_DAYS,),
        fetchall=True,
    )

    count = len(result) if result else 0
    logger.info(f"Cleanup complete: deleted {count} conversations older than {RETENTION_DAYS} days")
    return count


if __name__ == "__main__":
    try:
        deleted = cleanup_old_conversations()
        print(f"✅ Deleted {deleted} old conversations")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"❌ Cleanup failed: {e}")
    finally:
        close_pool()
