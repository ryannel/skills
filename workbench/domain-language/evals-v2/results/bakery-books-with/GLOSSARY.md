# Glossary

The agreed name for each thing in this project. Use these names in code, plans, tests and chat. An entry with a
`Proposed:` line hasn't been agreed by the human yet.

**Accounts Payable**
The money the bakery owes its suppliers for things it has received and not yet paid for, such as flour from the
mill.
Avoid: what I owe
Source: the standard bookkeeping term, used by QuickBooks, Xero and Sage
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Bank Balance**
The money in the bakery's bank account on a given day.
Source: the everyday banking and bookkeeping term
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Cash Book**
The book of every transaction the bakery makes, one line each, in date order.
Avoid: money log, log
Source: single-entry bookkeeping, where the cash book is the one book a small business keeps
Stored as: `MoneyLog` class in `src/money.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Category**
The heading a transaction is filed under, such as Ingredients, Wages or Bread Sales, so the money can be added up
by what it was for.
Not: the bank account. A category is a label on transactions; the bank account holds the money.
Avoid: pot
Source: QuickBooks calls these categories when you file a transaction; accountants call them accounts, and the
full list of them the chart of accounts
Stored as: `pot`, a field of `LogLine` in `src/money.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Money In / Money Out**
Whether a transaction brought money into the bakery or paid money out of it.
Source: the plain terms Xero and most banks use; a cash book calls them receipts and payments
Stored as: `"in"` and `"out"`, in the `direction` field of `LogLine` in `src/money.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Profit and Loss**
The month-end report that totals each category for the month, money in less money out, and shows what the bakery
made or lost.
Avoid: pot totals
Source: the standard small-business report, also called the income statement or P&L
Stored as: `pot_totals()` in `src/money.py`, which gives the category totals but not the bottom line
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Supplier**
A business the bakery buys from, such as the flour mill.
Avoid: vendor
Source: the usual bookkeeping term; QuickBooks in the US says vendor
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Transaction**
One line in the cash book: a date, an amount, money in or money out, and a category.
Avoid: log line, line, entry
Source: the term QuickBooks, Xero and single-entry bookkeeping guides use for each money movement
Stored as: `LogLine` class in `src/money.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

## Open questions

- "Where I stand": the bank balance set against accounts payable. The human hasn't named it, and it isn't clear
  which is taken from which. Nothing in `src/money.py` works it out yet.
- Flour bought on credit: is it a transaction when the flour arrives, or when the mill is paid? This decides which
  month's Ingredients it counts in.
