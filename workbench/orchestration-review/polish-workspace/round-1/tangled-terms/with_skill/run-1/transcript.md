# tangled-terms, with skill

## Owner

can we sort out the language in this project? there are a ton of terms floating around in the docs and I'm not sure what they all mean anymore

## Agent

I read the docs, the code and the data. Nothing is changed yet: the names are yours to pick, so here is what I found and what I'd recommend.

## Where the names clash

1. **One compartment has four names: "hopper", "locker", "unit" and "door".** I recommend **Locker**, because the code and the saved data already use it and it needs no explaining. "Door" would then mean only the physical door.
2. **The wall of lockers has two names: "bank" and "cabinet".** I recommend **Bank**, because the overview already treats "cabinet" as the stray. Which do you actually say?
3. **"Claimed" means two opposite things.** The status `claimed` means the parcel is in the locker and waiting, but "unclaimed parcels go stale" uses "claim" to mean the customer picking it up. I recommend calling the status **Awaiting Collection** and dropping "claimed" and "unclaimed" from the docs. The code and data would keep `claimed` as the stored value, noted in the glossary.
4. **The code the customer gets has no name.** What do you call it?
5. **"Stale" has a name but no clear meaning.** Who does the bank flag a stale parcel to, and what happens to the parcel next?

## How it would read with those names

1. The **Courier** scans in at the **Bank** and puts the **Parcel** in a free **Locker**. This is a **Drop-off**.
2. When the locker door shuts, the system marks the parcel **Awaiting Collection**.
3. The system sends the **Customer** a code (name to be agreed).
4. The customer enters the code, the locker opens and they take the parcel. The parcel is now **Collected**.
5. A parcel not collected within 72 hours becomes **Stale**, and the bank flags it.

I assumed "Courier", "Customer", "Parcel", "Collected" and "Drop-off" are undisputed; say so if any is wrong.

Once you answer 1–5, I'll write the agreed names into a `GLOSSARY.md` at the repo root and bring `docs/overview.md` in line with it. Nothing in the code or data would be renamed.

## Owner

1. I say "bank". 
2. I don't mind on the code name. 
3. I don't mind on what happens to a stale parcel either.

Your plan for Locker and Awaiting Collection is fine.

## Agent

The glossary is written and the overview now follows it. Nothing is committed.

- **`GLOSSARY.md`** (new, at the repo root) has ten entries: Courier, Customer, Parcel, Locker, Bank, Collection Code, Drop-off, Awaiting Collection, Collected and Stale.
- **`docs/overview.md`** is rewritten as the five numbered steps using those names. "Hopper", "unit", "cabinet" and "unclaimed" are gone from it.
- **`src/parcel.py`** has one docstring reworded, which said "hopper (the locker)". I said I wouldn't touch the code, but that comment would have kept the old word alive.
- **`AGENTS.md`** (new) is one line telling future sessions to read the glossary.

The stored value `claimed` is unchanged in the code and data. The remaining mentions of it in the docs and code are either the stored value itself or a note that says "stored as `claimed`".

Two things came from your "don't mind" answers:

- **Collection Code**: I picked this name for the code the customer gets, to match "Collected". It is marked as proposed in the glossary until you say it's fine.
- **Stale**: the entry says only what the old overview said, that the parcel wasn't collected within 72 hours and the bank flags it. Who gets flagged and what happens next is left undefined.

## Owner

Collection Code is fine by me, thanks.

## Agent

Collection Code is now an agreed entry: I removed its "proposed" mark, so all ten names in `GLOSSARY.md` are agreed.

The changes are still uncommitted. Say the word if you'd like me to commit them.

---

Ended: the agent finished and asked nothing.
