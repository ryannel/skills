from datetime import date, timedelta

def send_email(to: str, subject: str, body: str) -> None:
    print(f"to={to} subject={subject}")

def send_overdue_notices(loans, users, today: date) -> int:
    """Overdue Notice: the day after the due date, for loans not yet returned."""
    sent = 0
    for loan in loans:
        if loan["returned"] is None and loan["due"] + timedelta(days=1) == today:
            patron = users[loan["user_id"]]
            send_email(patron["email"], "Overdue: " + loan["title"], "Please return it.")
            sent += 1
    return sent
