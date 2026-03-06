from datetime import datetime, date

ALERT_LIMIT = 32


def determine_expiry_severity(entry, today):
    expiry = entry.get("expiry_date")
    if not expiry:
        return None
    due_days = (expiry - today).days
    is_meat = bool(entry.get("is_meat"))
    created_at = entry.get("created_at")
    if is_meat:
        if due_days <= 2:
            return "meat-urgent"
        if created_at:
            created_days = (today - created_at.date()).days
            if created_days >= 3:
                return "meat-stale"
        return None
    if due_days <= 7:
        return "standard-week"
    if due_days <= 30:
        return "standard-month"
    return None


def build_alert_payload(entry, severity, today):
    expiry = entry.get("expiry_date")
    due_days = (expiry - today).days if expiry else None
    return {
        "id": entry.get("id"),
        "sku": entry.get("sku"),
        "name": entry.get("name"),
        "expiry_date": expiry.isoformat() if isinstance(expiry, date) else None,
        "is_meat": bool(entry.get("is_meat")),
        "severity": severity,
        "due_in_days": due_days,
        "created_at": entry.get("created_at").isoformat() if entry.get("created_at") else None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
