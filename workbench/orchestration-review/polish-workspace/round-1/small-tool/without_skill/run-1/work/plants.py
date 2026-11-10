#!/usr/bin/env python3
"""Track which houseplants need water. Vocabulary follows GLOSSARY.md."""

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

OK, DUE, OVERDUE = "OK", "due", "overdue"


class PlantError(Exception):
    """A problem to report to the user without a traceback."""


# --- storage ---------------------------------------------------------------

def data_path():
    return Path(os.environ.get("PLANTS_FILE", Path.home() / ".plants.json"))


def load():
    path = data_path()
    if not path.exists():
        return {"plants": []}
    with path.open() as f:
        return json.load(f)


def save(data):
    path = data_path()
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    tmp.replace(path)


# --- domain ----------------------------------------------------------------

def today():
    override = os.environ.get("PLANTS_TODAY")  # for tests
    return date.fromisoformat(override) if override else date.today()


def parse_date(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise PlantError(f"'{text}' is not a date; use YYYY-MM-DD")


def positive_days(text):
    try:
        days = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' is not a whole number of days")
    if days < 1:
        raise argparse.ArgumentTypeError("days must be at least 1")
    return days


def find(data, name):
    for plant in data["plants"]:
        if plant["name"].lower() == name.lower():
            return plant
    raise PlantError(f"no plant named '{name}'")


def last_watered(plant):
    if not plant["waterings"]:
        return None
    return date.fromisoformat(max(plant["waterings"]))


def next_due(plant, now):
    """Last watered + interval, pushed back by any snooze.

    A plant with no waterings is due immediately.
    """
    last = last_watered(plant)
    due = last + timedelta(days=plant["interval"]) if last else now
    if plant.get("snoozed_until"):
        due = max(due, date.fromisoformat(plant["snoozed_until"]))
    return due


def status(plant, now):
    due = next_due(plant, now)
    if due > now:
        return OK
    return DUE if due == now else OVERDUE


def status_text(plant, now):
    state = status(plant, now)
    if state != OVERDUE:
        return state
    days = (now - next_due(plant, now)).days
    return f"{days} day{'s' if days != 1 else ''} overdue"


def in_room(plants, room):
    if room is None:
        return plants
    return [p for p in plants if p["room"].lower() == room.lower()]


# --- commands --------------------------------------------------------------

def cmd_add(args, data):
    if any(p["name"].lower() == args.name.lower() for p in data["plants"]):
        raise PlantError(f"there is already a plant named '{args.name}'")
    plant = {
        "name": args.name,
        "species": args.species,
        "room": args.room,
        "interval": args.every,
        "waterings": [],
        "snoozed_until": None,
    }
    if args.watered:
        watered = parse_date(args.watered)
        if watered > today():
            raise PlantError("a watering cannot be in the future")
        plant["waterings"].append(watered.isoformat())
    data["plants"].append(plant)
    save(data)
    print(f"Added {plant['name']} to {plant['room']}, every {plant['interval']} days.")


def cmd_water(args, data):
    now = today()
    when = parse_date(args.on) if args.on else now
    if when > now:
        raise PlantError("a watering cannot be in the future")
    plants = [find(data, name) for name in args.names]
    for plant in plants:
        if when.isoformat() not in plant["waterings"]:
            plant["waterings"].append(when.isoformat())
            plant["waterings"].sort()
        plant["snoozed_until"] = None
    save(data)
    for plant in plants:
        print(f"Watered {plant['name']}. Next due {next_due(plant, now)}.")


def cmd_snooze(args, data):
    now = today()
    plant = find(data, args.name)
    until = max(next_due(plant, now), now) + timedelta(days=args.days)
    plant["snoozed_until"] = until.isoformat()
    save(data)
    print(f"Snoozed {plant['name']}. Next due {until}.")


def cmd_list(args, data):
    now = today()
    plants = sorted(in_room(data["plants"], args.room), key=lambda p: next_due(p, now))
    if not plants:
        print("No plants.")
        return
    rows = [("NAME", "ROOM", "INTERVAL", "LAST WATERED", "NEXT DUE", "STATUS")]
    for p in plants:
        last = last_watered(p)
        rows.append((
            p["name"],
            p["room"],
            f"{p['interval']}d",
            str(last) if last else "never",
            str(next_due(p, now)),
            status_text(p, now),
        ))
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip())


def cmd_remind(args, data):
    now = today()
    needy = [p for p in in_room(data["plants"], args.room) if status(p, now) != OK]
    if not needy:
        print("No plants need water.")
        return
    needy.sort(key=lambda p: next_due(p, now))
    count = len(needy)
    print(f"{count} plant{'s' if count != 1 else ''} need{'s' if count == 1 else ''} water:")
    for p in needy:
        print(f"  {p['name']} ({p['room']}): {status_text(p, now)}")


def cmd_show(args, data):
    now = today()
    plant = find(data, args.name)
    last = last_watered(plant)
    print(f"Name:          {plant['name']}")
    if plant.get("species"):
        print(f"Species:       {plant['species']}")
    print(f"Room:          {plant['room']}")
    print(f"Interval:      every {plant['interval']} days")
    print(f"Last watered:  {last if last else 'never'}")
    print(f"Next due:      {next_due(plant, now)}")
    print(f"Status:        {status_text(plant, now)}")
    if plant["waterings"]:
        print("Waterings:")
        for day in reversed(plant["waterings"]):
            print(f"  {day}")


def cmd_rooms(args, data):
    now = today()
    rooms = {}
    for p in data["plants"]:
        total, needy = rooms.get(p["room"], (0, 0))
        rooms[p["room"]] = (total + 1, needy + (status(p, now) != OK))
    if not rooms:
        print("No rooms.")
        return
    for room in sorted(rooms, key=str.lower):
        total, needy = rooms[room]
        line = f"{room}: {total} plant{'s' if total != 1 else ''}"
        if needy:
            line += f", {needy} need{'s' if needy == 1 else ''} water"
        print(line)


def cmd_move(args, data):
    plant = find(data, args.name)
    plant["room"] = args.room
    save(data)
    print(f"Moved {plant['name']} to {args.room}.")


def cmd_schedule(args, data):
    now = today()
    plant = find(data, args.name)
    plant["interval"] = args.days
    save(data)
    unit = "day" if args.days == 1 else "days"
    print(f"{plant['name']} is now every {args.days} {unit}. Next due {next_due(plant, now)}.")


def cmd_remove(args, data):
    plant = find(data, args.name)
    data["plants"].remove(plant)
    save(data)
    print(f"Removed {plant['name']}.")


# --- cli -------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="plants", description="Track which houseplants need water."
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p = sub.add_parser("add", help="add a plant")
    p.add_argument("name")
    p.add_argument("--room", required=True, help="room the plant lives in")
    p.add_argument("--every", required=True, type=positive_days, metavar="DAYS",
                   help="interval: days between waterings")
    p.add_argument("--species")
    p.add_argument("--watered", metavar="DATE", help="date it was last watered (YYYY-MM-DD)")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("water", help="record a watering")
    p.add_argument("names", nargs="+", metavar="name")
    p.add_argument("--on", metavar="DATE", help="date of the watering (default: today)")
    p.set_defaults(func=cmd_water)

    p = sub.add_parser("snooze", help="push next due back without recording a watering")
    p.add_argument("name")
    p.add_argument("days", type=positive_days)
    p.set_defaults(func=cmd_snooze)

    p = sub.add_parser("list", help="list plants and their status")
    p.add_argument("--room")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("remind", help="show the plants that need water")
    p.add_argument("--room")
    p.set_defaults(func=cmd_remind)

    p = sub.add_parser("show", help="show one plant and its waterings")
    p.add_argument("name")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("rooms", help="list rooms")
    p.set_defaults(func=cmd_rooms)

    p = sub.add_parser("move", help="move a plant to another room")
    p.add_argument("name")
    p.add_argument("room")
    p.set_defaults(func=cmd_move)

    p = sub.add_parser("schedule", help="change a plant's interval")
    p.add_argument("name")
    p.add_argument("days", type=positive_days)
    p.set_defaults(func=cmd_schedule)

    p = sub.add_parser("remove", help="remove a plant and its waterings")
    p.add_argument("name")
    p.set_defaults(func=cmd_remove)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args, load())
    except PlantError as err:
        print(f"plants: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
