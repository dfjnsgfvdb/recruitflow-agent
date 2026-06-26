NULLABLE_STRING = {"type": ["string", "null"]}

INTENT_ENUM = [
    "CREATE_CANDIDATE",
    "SCHEDULE_INTERVIEW",
    "UPDATE_STAGE",
    "REJECT_CANDIDATE",
    "QUERY_PROGRESS",
    "UNKNOWN",
]

STAGE_ENUM = [
    "NEW",
    "RESUME_PASSED",
    "FIRST_INTERVIEW_PENDING",
    "SECOND_INTERVIEW_PENDING",
    "HR_INTERVIEW_PENDING",
    "FINAL_INTERVIEW_PENDING",
    "INTERVIEW_PENDING",
    "INTERVIEW_PASSED",
    "OFFER_PENDING",
    "OFFER_SENT",
    "REJECTED",
    "HIRED",
    None,
]

TOOL_ENUM = [
    "create_or_update_candidate",
    "create_interview",
    "update_candidate_stage",
    "reject_candidate",
    "get_dashboard_summary",
    "query_dashboard",
    "send_notice",
    "sync_candidate",
]

RECRUITMENT_AGENT_JSON_SCHEMA = {
    "name": "recruitment_agent_result",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "intent",
            "confidence",
            "candidate",
            "stage_change",
            "interview",
            "query",
            "actions",
            "need_clarification",
            "clarification_questions",
        ],
        "properties": {
            "intent": {"type": "string", "enum": INTENT_ENUM},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "candidate": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "name",
                    "phone",
                    "email",
                    "position_name",
                    "source",
                    "education",
                    "school",
                    "experience_summary",
                    "owner",
                ],
                "properties": {
                    "name": NULLABLE_STRING,
                    "phone": NULLABLE_STRING,
                    "email": NULLABLE_STRING,
                    "position_name": NULLABLE_STRING,
                    "source": NULLABLE_STRING,
                    "education": NULLABLE_STRING,
                    "school": NULLABLE_STRING,
                    "experience_summary": NULLABLE_STRING,
                    "owner": NULLABLE_STRING,
                },
            },
            "stage_change": {
                "type": "object",
                "additionalProperties": False,
                "required": ["old_stage", "new_stage", "reason"],
                "properties": {
                    "old_stage": {"type": ["string", "null"], "enum": STAGE_ENUM},
                    "new_stage": {"type": ["string", "null"], "enum": STAGE_ENUM},
                    "reason": NULLABLE_STRING,
                },
            },
            "interview": {
                "type": "object",
                "additionalProperties": False,
                "required": ["round", "interview_time", "interviewer", "location", "result", "feedback"],
                "properties": {
                    "round": {"type": ["string", "null"], "enum": ["FIRST", "SECOND", "HR", "FINAL", None]},
                    "interview_time": NULLABLE_STRING,
                    "interviewer": NULLABLE_STRING,
                    "location": NULLABLE_STRING,
                    "result": {"type": ["string", "null"], "enum": ["PENDING", "PASSED", "FAILED", "CANCELLED", None]},
                    "feedback": NULLABLE_STRING,
                },
            },
            "query": {
                "type": "object",
                "additionalProperties": False,
                "required": ["position_name", "time_range", "metric"],
                "properties": {
                    "position_name": NULLABLE_STRING,
                    "time_range": NULLABLE_STRING,
                    "metric": NULLABLE_STRING,
                },
            },
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["tool", "args", "risk_level"],
                    "properties": {
                        "tool": {"type": "string", "enum": TOOL_ENUM},
                        "args": {"type": "object"},
                        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                    },
                },
            },
            "need_clarification": {"type": "boolean"},
            "clarification_questions": {"type": "array", "items": {"type": "string"}},
        },
    },
    "strict": True,
}
