from datetime import datetime


def fformat(f):
    return f"{f:.6f}" if f is not None else ""


def dtformat(dt: str | datetime) -> str:
    if not dt:
        return ""

    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)

    return dt.strftime("%Y-%m-%d %H:%M")
