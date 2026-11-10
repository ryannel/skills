STATES = ("claimed", "collected", "stale")

def drop(locker_id, parcel):
    """Drop-off: put the parcel in the locker and mark it Awaiting Collection (stored as "claimed")."""
    return {"locker": locker_id, "parcel": parcel, "state": "claimed"}
