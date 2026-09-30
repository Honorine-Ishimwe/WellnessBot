"""
Cleanup job: Delete conversations older than 30 days.
Run as a Render Cron Job: python cleanup_job.py
Schedule: 0 3 * * * (daily at 3 AM UTC)
"""

from dotenv import load_dotenv

load_dotenv()

from backend.config import RETENTION_DAYS
from backend.repositories import conversation_repo
from backend.db import close_pool
from backend.middleware.logging import logger


def cleanup_old_conversations():
    """Delete conversations older than RETENTION_DAYS."""
    result = conversation_repo.delete_older_than(RETENTION_DAYS)

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
