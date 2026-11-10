STATES = ("claimed", "collected", "stale")

def drop(locker_id, parcel):
    """Drop-off: a courier puts the parcel in a locker. It is then Waiting for Pickup."""
    return {"locker": locker_id, "parcel": parcel, "state": "claimed"}


def redrop(record, new_locker_id):
    """Re-drop: the first locker's door is jammed, so the courier puts the parcel
    in a different locker. The parcel is still Waiting for Pickup."""
    if record["state"] != "claimed":
        raise ValueError("only a parcel that is Waiting for Pickup can be re-dropped")
    if new_locker_id == record["locker"]:
        raise ValueError("a re-drop must go to a different locker")
    return {**record, "locker": new_locker_id, "jammed_locker": record["locker"]}
