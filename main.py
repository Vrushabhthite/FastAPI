from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import psycopg2
import psycopg2.extras
import logging
import sys

from db import get_db_connection

# ----------------- LOGGING -----------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# ----------------- APP -----------------
app = FastAPI(title="USO Minimal API")

# ----------------- REQUEST SCHEMA -----------------
class USORequest(BaseModel):
    osmOrderId: str
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    vendor: Optional[str] = None
    uniqueId: Optional[str] = None
    circle: Optional[str] = None
    crActivity: Optional[str] = None
    crDate: Optional[str] = None
    proposedStart: Optional[str] = None
    phase: str
    payload: Dict[str, Any]

# ----------------- API -----------------
@app.post("/uso/process", status_code=status.HTTP_202_ACCEPTED)
def process_uso(request: USORequest):
    conn = None
    try:
        logger.info(f"Received USO request | osmOrderId={request.osmOrderId}")
        conn = get_db_connection()

        try:
            proposed_start = (
                datetime.fromisoformat(request.proposedStart)
                if request.proposedStart else None
            )
            sysmodtime = (
                datetime.fromisoformat(request.crDate)
                if request.crDate else None
            )
        except ValueError as dt_err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {dt_err}"
            )

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # ---------- CHECK EXISTENCE ----------
            cur.execute(
                """
                SELECT crtid
                FROM public.osm_cr_dump
                WHERE crtid = %s
                """,
                (request.osmOrderId,)
            )
            exists = cur.fetchone()

            if exists:
                logger.info("Updating existing record")

                cur.execute(
                    """
                    UPDATE public.osm_cr_dump
                    SET
                        domain = %s,
                        subdomain = %s,
                        vendor = %s,
                        unique_id = %s,
                        location_full_name = %s,
                        cractivity = %s,
                        sysmodtime = %s,
                        proposed_start = %s,
                        phase = %s,
                        payload = %s,
                        updated_at = NOW()
                    WHERE crtid = %s
                    """,
                    (
                        request.domain,
                        request.subdomain,
                        request.vendor,
                        request.uniqueId,
                        request.circle,
                        request.crActivity,
                        sysmodtime,
                        proposed_start,
                        request.phase,
                        psycopg2.extras.Json(request.payload),
                        request.osmOrderId
                    )
                )
            else:
                logger.info("Creating new record")

                cur.execute(
                    """
                    INSERT INTO public.osm_cr_dump (
                        crtid,
                        domain,
                        subdomain,
                        vendor,
                        unique_id,
                        location_full_name,
                        cractivity,
                        sysmodtime,
                        proposed_start,
                        phase,
                        payload,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW()
                    )
                    """,
                    (
                        request.osmOrderId,
                        request.domain,
                        request.subdomain,
                        request.vendor,
                        request.uniqueId,
                        request.circle,
                        request.crActivity,
                        sysmodtime,
                        proposed_start,
                        request.phase,
                        psycopg2.extras.Json(request.payload)
                    )
                )

        conn.commit()
        logger.info(f"DB commit successful | osmOrderId={request.osmOrderId}")

        return {
            "osmOrderId": request.osmOrderId,
            "status": "accepted",
            "executionMode": "Auto"
        }

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()

        exc_type, _, exc_tb = sys.exc_info()
        line_no = exc_tb.tb_lineno
        file_name = exc_tb.tb_frame.f_code.co_filename

        logger.error(
            f"Unhandled Exception | File={file_name} | Line={line_no}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "file": file_name,
                "line": line_no,
                "type": exc_type.__name__
            }
        )

    finally:
        if conn:
            conn.close()
