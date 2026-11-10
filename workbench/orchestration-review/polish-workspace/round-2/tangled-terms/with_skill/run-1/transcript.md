# tangled-terms, with skill

## Owner

can we sort out the language in this project? there are a ton of terms floating around in the docs and I'm not sure what they all mean anymore

## Agent

I read everything in the project (`docs/overview.md`, `src/parcel.py`, `data/parcels.json`). There are about a dozen terms, and three of them are tangled.

- **One compartment has four names.** The overview says the parcel goes in the "hopper", then defines a "unit" as "one door". The code calls it a `locker` and has a comment reading "the hopper (the locker)".
- **The wall of compartments has two names.** The overview calls it a "bank" and notes that "some docs say cabinet".
- **"Claimed" contradicts itself.** A parcel becomes "claimed" when the courier shuts the door, so it means "dropped off, waiting for pickup". But the next sentence says "unclaimed parcels go stale after 72h", where "unclaimed" means "not picked up yet". By the first meaning, those parcels are claimed. The code and the saved data both store `claimed` as the state.

The remaining terms look consistent, but most appear in only one place: courier, customer, code, "scans in", stale, flags, and `collected` (which is in the code but not the docs).

Before I suggest any names, I'd like to hear yours, so the glossary uses the words you actually use and not ones I made up.

**In your own words, what happens to a parcel from the moment the courier arrives to the moment it's gone?** Include the case where nobody comes for it. A few rough sentences are enough.

From that I'll write the flow back as numbered steps with one name per thing, and you can correct any that read wrong. Once you agree, I'll write the glossary and bring the overview in line with it. The stored `claimed` value in the code and data stays as it is unless you ask for a rename.

## Owner

A courier drops a parcel in a locker and shuts the door. The customer gets a code and scans it at the bank to pick it up. If nobody picks it up within 3 days, it's overdue.

## Agent

Your telling settles most of it. Here are the names I took from it, and what each one replaces.

| Name | Meaning | Replaces | Stored in code and data as |
|---|---|---|---|
| **Courier** | The person who delivers a parcel | | |
| **Parcel** | The thing being delivered | | `parcel` |
| **Locker** | One compartment with one door | hopper, unit | `locker` |
| **Bank** | A wall of lockers | cabinet | |
| **Customer** | The person the parcel is for | | |
| **Code** | What the customer scans to open the locker | | |
| **Picked Up** | The customer has taken the parcel | collected | `collected` |
| **Overdue** | Nobody picked the parcel up within 3 days | stale, unclaimed | `stale` |

Here is the flow written with those names:

1. The **Courier** puts a **Parcel** in a **Locker** and shuts the door.
2. The Parcel is now ______, the state the docs and code call "claimed".
3. The **Customer** gets a **Code**.
4. The Customer scans the Code at the **Bank**, the Locker opens, and the Parcel is **Picked Up**.
5. If the Parcel is not Picked Up within 3 days, it is **Overdue**.

Two things are still open:

1. **The blank in step 2.** What do you call a parcel that is sitting in a locker and hasn't been picked up yet? If you have no word for it, I'd suggest "Awaiting Pickup". Whatever you choose, "claimed" goes on the avoid list, because it reads as if the customer already has the parcel.
2. **Two things the overview mentions that you didn't.** It says the courier "scans in" before the drop, and that the bank "flags" overdue parcels. Are those real steps? If so, what does the courier scan, and what does flagging do?

If the names and steps read right, answer those two and I'll write `GLOSSARY.md` and rewrite the overview to match. The stored values `claimed`, `collected` and `stale` stay as they are, and the glossary records them against the new names.

## Owner

"Awaiting Pickup" works, that's what I'd call it. The names and steps read right to me. On the scanning in and flagging, I don't mind.

## Agent

The glossary is written and the overview now follows it. Nothing is committed yet.

- **`GLOSSARY.md`** (new, at the project root) has the nine agreed names: Courier, Customer, Parcel, Locker, Bank, Code, Awaiting Pickup, Picked Up and Overdue. Each entry lists the old names to avoid and, for the three states, the value the code stores.
- **`docs/overview.md`** is rewritten as the five numbered steps you agreed, using only those names. Each stored value (`claimed`, `collected`, `stale`) is mentioned once, next to the state it belongs to.
- **`AGENTS.md`** (new) is one line telling any future agent session to read the glossary first.

Since you didn't mind either way, "scans in" and "flags" stay in the overview as plain words and have no glossary entries.

I searched the docs for every avoided name. The only matches left are the three stored values in the overview.

I left the code and data alone, so two things there still use the old words:

- **The comment in `src/parcel.py` line 4** still says "put the parcel in the hopper (the locker) and mark it claimed". Updating it is a one-line change if you want it.
- **The stored state values** are still `claimed`, `collected` and `stale` in `src/parcel.py` and `data/parcels.json`. Renaming them means changing the saved records too, so that is a separate piece of work if you want it.

---

Ended: the agent finished and asked nothing.
