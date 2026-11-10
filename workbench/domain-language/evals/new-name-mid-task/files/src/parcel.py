STATES = ("claimed", "collected", "stale")

def drop(locker_id, parcel):
    """Drop-off: a courier puts the parcel in a locker. It is then Waiting for Pickup."""
    return {"locker": locker_id, "parcel": parcel, "state": "claimed"}
