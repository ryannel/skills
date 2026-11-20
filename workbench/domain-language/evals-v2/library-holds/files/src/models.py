HOLD_DAYS = 3  # how long a claimed book waits before it goes back on the shelf

STATUSES = ("available", "claimed", "out", "late")

USERS_TABLE = "users"   # id, name, card_number
LOANS_TABLE = "loans"   # id, user_id, book_id, status, due

def expire_claims(loans, today):
    """A claimed book that nobody has collected for HOLD_DAYS goes back to available."""
    for loan in loans:
        if loan["status"] == "claimed" and (today - loan["since"]).days >= HOLD_DAYS:
            loan["status"] = "available"
