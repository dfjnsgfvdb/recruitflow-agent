def send_notice(message: str) -> dict:
    return {
        "target": "WECOM",
        "status": "SUCCESS",
        "message": message,
    }
