STATES = ("claimed", "collected", "stale")

def drop(locker_id, parcel):
    """Courier drop: put the parcel in the hopper (the locker) and mark it claimed."""
    return {"locker": locker_id, "parcel": parcel, "state": "claimed"}
