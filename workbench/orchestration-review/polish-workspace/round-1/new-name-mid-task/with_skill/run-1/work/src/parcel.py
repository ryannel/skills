STATES = ("claimed", "collected", "stale")

def drop(locker_id, parcel):
    """Drop-off: a courier puts the parcel in a locker. It is then Waiting for Pickup."""
    return {"locker": locker_id, "parcel": parcel, "state": "claimed"}


def move_to_another_locker(dropped, new_locker_id):
    """Move to Another Locker: a courier puts a parcel that is Waiting for Pickup
    into a different locker, because the door of the first locker is jammed.

    Takes the record that drop() returned, and returns a new record for the
    new locker. The parcel is still Waiting for Pickup. `moved_from` holds the
    locker with the jammed door.
    """
    if dropped["state"] != "claimed":
        raise ValueError("only a parcel that is Waiting for Pickup can be moved to another locker")
    if new_locker_id == dropped["locker"]:
        raise ValueError("the new locker must be a different locker")
    return {**dropped, "locker": new_locker_id, "moved_from": dropped["locker"]}
