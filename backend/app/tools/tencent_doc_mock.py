from app.db.models import Candidate


def sync_candidate(candidate: Candidate) -> dict:
    return {
        "target": "TENCENT_DOC",
        "status": "SUCCESS",
        "operation": "UPSERT_CANDIDATE",
        "candidate_name": candidate.name,
    }
