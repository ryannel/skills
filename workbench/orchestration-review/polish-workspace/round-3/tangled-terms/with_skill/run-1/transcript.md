# tangled-terms, with skill

## Owner

can we sort out the language in this project? there are a ton of terms floating around in the docs and I'm not sure what they all mean anymore

## Agent

I read the docs, code and data (they're tiny: `docs/overview.md`, `src/parcel.py`, `data/parcels.json`). Nothing is changed yet, and the tangle is real.

- **The compartment a parcel goes into has four names.** The doc calls it "hopper" and "unit" ("a unit is one door"), and the code calls it "locker" and `locker_id`.
- **The wall of compartments has two names.** The doc uses "bank" and notes that "some docs say cabinet".
- **"Claimed" is used in two opposite senses.** In the doc and the code, a parcel becomes `claimed` when the courier shuts the door, meaning it is waiting inside. The next sentence says "unclaimed parcels go stale after 72h", where "unclaimed" means the customer hasn't picked it up. By the first meaning, the parcels that go stale are the claimed ones.
- **Some words are used once and never explained.** These are "scans in", "code", "stale", "flags" and "collected" (a state in the code that the doc never mentions).

Before I suggest any names, I'd like yours, so the glossary matches how you actually talk about this.

**In your own words, what happens from the moment a courier arrives with a parcel to the moment it's either picked up or left too long?** A few rough sentences are plenty.

From that I'll write the flow back as numbered steps with one name per thing, and you can correct any that read wrong. Once you agree, I'll write `GLOSSARY.md` at the repo root and update the overview doc to match. The stored names (such as `claimed` in the code and in `parcels.json`) will stay as they are, and the glossary will record them.

## Owner

A courier comes with a parcel and puts it in a locker, one door in a bank. Then the customer gets a code and comes to do a pickup. If nobody collects it within 3 days, it's overdue.

## Agent

That settles most of it. I've started `GLOSSARY.md` at the repo root with the three names your telling fixed:

- **Locker**: one door in a bank, and the space behind it. It replaces "hopper" and "unit".
- **Bank**: a wall of lockers. It replaces "cabinet".
- **Overdue**: a parcel nobody has collected within 3 days. It replaces "stale"; the code and data keep `stale`, and the glossary records that.

Here is the flow in your words:

1. The courier puts the parcel in a locker, which is one door in a bank.
2. The customer gets a code.
3. The parcel waits in the locker. *(This status has no name yet.)*
4. The customer comes with the code and does a pickup. The parcel is then collected.
5. If nobody collects the parcel within 3 days, it is overdue.

Three things are still open:

1. **What do you call a parcel in step 3**, sitting in the locker and not yet picked up? The code stores this as `claimed`, which is the word that caused the confusion.
2. **"Pickup" and "collected"**: you used both. I recommend "pickup" for the customer's visit and "collected" for the parcel's status afterwards, since the code already stores `collected`. Is that right?
3. **"Scans in" and "flags"**: the doc says the courier "scans in" first and that the bank "flags" overdue parcels. You mentioned neither. Are those real steps that need names, or should I drop them from the doc?

Once you answer, I'll finish the glossary and rewrite `docs/overview.md` to match. I haven't touched the overview, the code or the data.

## Owner

Step 3 is "waiting for pickup". Yes, "pickup" for the visit and "collected" for the status afterwards is fine. I don't mind about "scans in" and "flags".

## Agent

The language is sorted: the glossary is finished and the overview doc now follows it. Nothing is committed.

The seven agreed names, in `GLOSSARY.md` at the repo root:

| Name | Meaning | Replaces | Stored as |
|---|---|---|---|
| **Bank** | A wall of lockers | cabinet | |
| **Locker** | One door in a bank, and the space behind it | hopper, unit | |
| **Code** | What the customer gets when their parcel is put in a locker, and brings to the pickup | | |
| **Waiting for Pickup** | Status of a parcel in a locker that has not been collected | claimed, unclaimed | `claimed` |
| **Pickup** | The customer's visit, with their code, to take their parcel | | |
| **Collected** | Status of a parcel after the pickup | | |
| **Overdue** | Status of a parcel nobody has collected within 3 days | stale | `stale` |

What changed in the repo:

- **`docs/overview.md`** is rewritten as the five numbered steps you agreed, using only these names. It gives the stored names `claimed` and `stale` once each, where the reader meets those statuses.
- **"Scans in" and "flags" are dropped** from the overview, since you didn't mind. The old wording is still in git history if you want either back.
- **`AGENTS.md`** is new, with one line telling future sessions to read the glossary first.

The code and data are untouched, so `claimed` and `stale` are still what `src/parcel.py` and `data/parcels.json` store. One code comment still uses the old words: the docstring at `src/parcel.py:4` says "put the parcel in the hopper (the locker) and mark it claimed". I left it because you asked about names, not code changes; say if you want it reworded.

Renaming the stored values themselves (`claimed` to something like `waiting_for_pickup`) would be a real code and data change, so I haven't done it.

## Owner

I still can't tell how these fit together. Can you show me the terms used in sentences?

## Agent

Here is one parcel followed from start to finish, with each glossary name in bold. The parcel and locker come from your data file (`P-1`, locker 12); the days are made up for the example.

**The places**

- A **bank** is a wall of **lockers**. Each **locker** is one door with a space behind it.
- Locker 12 is one **locker** in a **bank**.

**The story of parcel P-1**

1. On Monday morning a courier puts parcel P-1 in **locker** 12 and shuts the door.
2. From that moment, P-1 is **waiting for pickup**. (The data file shows this as `claimed`.)
3. The customer gets a **code**.
4. From here the story ends one of two ways:
   - **The customer comes in time.** On Tuesday the customer comes to the **bank** with their **code** and does a **pickup**. P-1 is now **collected**.
   - **Nobody comes.** By Thursday morning 3 days have passed with no **pickup**. P-1 is now **overdue**. (The data file would show this as `stale`.)

**How the names relate**

- **Bank** and **locker** are places: the wall, and one door in it.
- **Code** is the thing the customer holds.
- **Pickup** is an event: the customer's visit.
- **Waiting for pickup**, **collected** and **overdue** are the three statuses a parcel can have. Every parcel in a locker starts as **waiting for pickup** and then becomes either **collected** or **overdue**.

One thing neither the old doc nor the code says is what happens to an **overdue** parcel next, for example whether the customer can still do a **pickup**. If that has an answer, tell me and I'll add it to the overview.

If this version reads more clearly, I can put the worked example into `docs/overview.md` under the numbered steps.

## Owner

That reads right, and it makes sense now. Yes, put it in the overview. I don't mind what happens to an overdue parcel next.

## Agent

The worked example is now in `docs/overview.md`, under the numbered steps, in two new sections: "An example" (the story of parcel P-1) and "How the names relate". I left out what happens to an overdue parcel next, as you said.

The repo now has three uncommitted changes: the new `GLOSSARY.md`, the new `AGENTS.md`, and the rewritten overview. Say if you'd like me to commit them.

---

Ended: the agent finished and asked nothing.
