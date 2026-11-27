"""Build the observability page data from the plans, flow and saved delivery history."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from itertools import pairwise
from statistics import median
import json
from pathlib import Path
import re
import subprocess

USER_REASONS = {"needs_access", "needs_hardware", "needs_context", "needs_feedback", "needs_human_feedback"}
ROLE = {"build": "builder", "review": "reviewer", "plan": "planner"}


def iso(date):
    return date.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def module_name(module, design_text):
    """A short human name for a module, from its design's title.

    Designs may open with "# Name: what it does" or "# Name (G3c)". Take the part before
    the colon or dash and drop goal codes. If that is just the module's code again, spell the
    code out ("GAME-UI" -> "Game UI").
    """
    parts = module.split("-")
    spelled = " ".join(part if any(c.isdigit() for c in part) or part in ("UI", "SDK")
                       else part.capitalize() if index == 0 else part.lower()
                       for index, part in enumerate(parts))
    title = next((line[2:].strip() for line in design_text.splitlines() if line.startswith("# ")), "")
    title = re.split(r":|\s[—–]\s", title)[0]
    title = re.sub(r"\s*\((?:G\d+\w*)\)\s*", " ", title).strip()
    if not title or title.isupper() or title.replace(" ", "-").upper() == module and title.upper() == title:
        return spelled
    return title


def ref(module, wp):
    if module and wp and re.fullmatch(r"(?:WP|M|U)\d+", wp):
        return f"{module.upper()}:" + re.sub(r"^M", "WP", wp)
    return None


def at(entry):
    return entry.get("at") if isinstance(entry, dict) else entry


def total_known(values):
    known = [value for value in values if value is not None]
    return round(sum(known), 4) if known else None


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, errors="replace").stdout


@lru_cache(maxsize=4)
def file_history(root, plans, head):
    """Read each changed blob once, including parent blobs from renames."""
    if not head:
        return [], {}
    raw = git(root, "-c", "core.quotePath=false", "log", "--first-parent", "--diff-merges=first-parent", "--raw",
              "--no-abbrev", "-M", "--format=%x1e%H%x1f%cI%x1f%s", head, "--", str(plans))
    proc = subprocess.Popen(["git", "-C", str(root), "cat-file", "--batch"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    @lru_cache(maxsize=None)
    def definitions(blob):
        if set(blob) == {"0"}:
            return {}
        proc.stdin.write((blob + "\n").encode())
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) != 3:
            return {}
        body = proc.stdout.read(int(header[2]))
        proc.stdout.read(1)
        try:
            data = json.loads(body)
            rows = data.get("work_packages", data.get("milestones", []))
            return {re.sub(r"^M", "WP", row["id"]): definition(row) for row in rows}
        except (ValueError, AttributeError, KeyError, TypeError):
            return {}  # a past commit can hold a draft, or use a layout the page doesn't read

    changes = []
    introduced = {}
    try:
        for block in filter(str.strip, raw.split("\x1e")):
            header, *files = block.strip("\n").splitlines()
            commit, date, subject = header.split("\x1f", 2)
            date = iso(instant(date))
            modules, edited = set(), set()
            design_changed = False
            files_changed = set()
            for line in files:
                meta, *paths = line.split("\t")
                if not meta.startswith(":"):
                    continue
                path = Path(paths[-1].strip('"'))
                if not path.is_relative_to(plans):
                    continue
                relative = path.relative_to(plans)
                if relative in {Path("VISION.md"), Path("ARCHITECTURE.md")}:
                    files_changed.add(relative.name)
                    continue
                if len(relative.parts) < 2:
                    continue
                module = relative.parts[0].upper()
                modules.add(module)
                if len(relative.parts) != 2:
                    continue
                filename = relative.name
                design_changed |= filename == "DESIGN.md" and meta.split()[2] != meta.split()[3]
                if filename == "DONE.json":
                    old, new = meta.split()[2:4]
                    before, after = definitions(old), definitions(new)
                    edited.update(f"{module}:{wp}" for wp in before.keys() | after.keys()
                                  if before.get(wp) != after.get(wp))
                    for wp in after.keys() - before.keys():
                        introduced[f"{module}:{wp}"] = date
            if modules or files_changed or files:
                changes.append(dict(at=date, commit=commit, subject=subject, modules=sorted(modules),
                                    definitions_changed=sorted(edited), design_changed=design_changed,
                                    **({"files": sorted(files_changed)} if files_changed else {})))
    finally:
        proc.stdin.close()
        proc.stdout.close()
        proc.wait()
    return changes, introduced


def definition(row):
    item_fields = ("statement", "check", "inspect", "ask", "lock", "target")
    return {
        "name": row.get("name"),
        "quality_bar": row.get("quality_bar"),
        "depends_on": [re.sub(r":M(?=\d+$)", ":WP", dep) for dep in row.get("depends_on", [])],
        "items": [(re.sub(r"^M(?=\d)", "WP", item["id"]),
                   [item.get(key) for key in item_fields]) for item in row.get("items", [])],
    }


def choices(root, path, pattern, text):
    matching = [match.groups() for line in text.splitlines() if (match := pattern.match(line))]
    if not matching:
        return []
    lines = git(root, "blame", "--line-porcelain", "--", str(path))
    date = None
    found = []
    for line in lines.splitlines():
        if line.startswith("author-time "):
            date = iso(datetime.fromtimestamp(int(line.split()[1]), timezone.utc))
        elif line.startswith("\t") and (match := pattern.match(line[1:])):
            found.append((match.groups(), date))
    return found or [(choice, None) for choice in matching]


def sessions_from(dash):
    turns = defaultdict(list)
    for values in dash.get("turns", {}).get("rows", []):
        turn = dict(zip(dash["turns"]["columns"], values))
        turns[turn["s"]].append(turn)

    outcomes = defaultdict(list)
    outcome_roles = {"READY_FOR_REVIEW": "build", "REVIEWED": "review",
                     "BLOCKED": "build", "PLANNED": "plan", "CHECKS_FAILED": "build"}
    for event in dash.get("events", []):
        if event.get("result"):
            role = event.get("role") or outcome_roles.get(event["result"])
            outcomes[role, ref(event.get("module"), event.get("work_package"))].append(event)

    sessions, costs = [], defaultdict(list)
    for index, session in enumerate(dash.get("sessions", [])):
        role = session.get("role")
        host, model = session.get("host"), session.get("model")
        kind = ROLE.get(role, session["kind"])
        related = sorted(turns[index], key=lambda turn: turn["start"])
        cost = total_known(turn.get("usd") for turn in related)
        costs[host, kind, model].append(cost)
        if role not in ROLE or session["kind"] != "script":
            continue
        key = ref(session.get("module"), session.get("work_package"))
        end = session.get("end")
        close = instant(end) if end else None
        start = instant(session["start"])
        candidates = [event for event in outcomes[role, key]
                      if close and start <= instant(event["at"]) <= close + timedelta(minutes=3)]
        result = max(candidates, key=lambda event: event["at"], default=None)
        ended = related[-1].get("ended") if related else None
        if result:
            outcome = result.get("verdict") or result["result"]
            ended = str(outcome).lower()
        sessions.append(dict(kind=kind, start=session["start"], end=end, host=host, model=model,
                             module=session.get("module"), ref=key, ended=ended, cost=cost,
                             id=session["session"], historical=True))
    return sessions, [dict(host=h, kind=k, model=m, cost=total_known(values), sessions=len(values),
                           priced=sum(v is not None for v in values))
                      for (h, k, m), values in costs.items()]


def waiting_from(flow):
    waiting = {}
    for line in flow.get("not_moving", []):
        match = re.match(r"([A-Z0-9_.-]+) (WP\d+|U\d+): (.+)", line)
        if not match:
            continue
        module, wp, detail = match.groups()
        reason = "none"
        for words, kind in [(r"needs_(access|hardware|context|feedback)", "user"),
                            (r"\block\b", "lock"), (r"\bmerge\b", "merge"),
                            (r"ready for review", "review"), (r"fail|blocked|error", "failure"),
                            (r"waiting, on|dependency", "dependency")]:
            if re.search(words, detail, re.I):
                reason = kind
                break
        waiting[ref(module, wp)] = dict(on=reason, detail=detail, since=None)
    return waiting


def flow_age(detail, snapshot):
    match = re.search(r"\bfor ((?:\d+[dhms] ?)+)\s*$", detail)
    if match:
        seconds = sum(int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
                      for n, u in re.findall(r"(\d+)([dhms])", match[1]))
        return iso(snapshot - timedelta(seconds=seconds))
    return None


MILESTONE_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MILESTONE_LINE = re.compile(r"-\s+\*\*(.+?)\*\*\s+\(`milestone/(" + MILESTONE_SLUG.pattern
                            + r")`([^)]*)\)\.?\s*(.*)")


def section(text, heading):
    match = re.search(r"^##[ \t]+(?:" + heading + r")[ \t]*$\n(.*?)(?=^#{1,2}[ \t]|\Z)", text,
                      re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return match[1].strip() if match else ""


def milestones_in(vision):
    """The milestone lines in vision order. Only a valid 'closed YYYY-MM-DD' note records a date."""
    milestones = {}
    lines = section(vision, r"(?:the )?milestones")
    for item in re.finditer(r"^- [^\n]*(?:\n[ \t]+[^\n]+)*", lines, re.MULTILINE):
        if match := MILESTONE_LINE.fullmatch(" ".join(item[0].split())):
            name, slug, notes, about = match.groups()
            closed_at = None
            if date := re.search(r"(?:^|,)[ \t]*closed (\d{4}-\d{2}-\d{2})[ \t]*(?:,|$)", notes):
                try:
                    closed_at = datetime.strptime(date[1], "%Y-%m-%d").date().isoformat()
                except ValueError:
                    pass
            milestones[slug] = (name, about, closed_at)
    return milestones


def milestone_rows(vision, modules, packages, introduced, sessions):
    previous = {}
    for module in modules:
        previous.update({later: earlier for earlier, later in pairwise(module["work_packages"])})

    edges = {key: list(dict.fromkeys([*wp["depends_on"], *([previous[key]] if key in previous else [])]))
             for key, wp in packages.items()}

    def ancestry(key):
        pending, seen = [key], set()
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending.extend(edges[current])
        return seen

    chains, visiting = {}, set()

    def chain(key):
        if key in visiting or packages[key]["status"] == "done":
            return []
        if key not in chains:
            visiting.add(key)
            chains[key] = max((chain(dep) for dep in edges[key]), key=len, default=[]) + [key]
            visiting.remove(key)
        return chains[key]

    closers = {}
    for key, wp in packages.items():
        if label := wp["closes"]:
            closers.setdefault(label, key)
    result = []
    for label, (name, about, closure) in milestones_in(vision).items():
        closer = closers.get(label)
        closure = None if closer else closure
        needed = ancestry(closer) if closer else set()
        needs = [key for key in packages if key in needed]
        left = [key for key in needs if packages[key]["status"] != "done"]
        timestamp = max((packages[key]["done_at"] for key in needs if packages[key]["done_at"]), default=None)
        dates = [introduced[key] for key in needs if key in introduced]
        baseline = introduced.get(closer)
        retro = None
        if needs and not left:
            in_cone = set(needs)
            runs = [run for run in sessions if run["ref"] in in_cone and
                    (not timestamp or run["start"] <= timestamp)]
            starts = [run["start"] for run in runs] + [packages[key]["started_at"] for key in needs
                                                       if packages[key]["started_at"]]
            failures = Counter(packages[key]["module"] for key in needs for review in packages[key]["reviews"]
                               if review["verdict"] == "fail" and
                               (not timestamp or (review["at"] or "") <= timestamp))
            cone_modules = {packages[key]["module"] for key in needs}
            design_changes = Counter(
                module["id"] for module in modules if module["id"] in cone_modules
                for review in module["design_history"] if review["verdict"] == "changes" and baseline and
                timestamp and baseline <= (review.get("at") or "") <= timestamp
            )
            review_hosts = Counter(
                (kind, review.get("host") or "Unknown")
                for kind, rows, verdict in (
                    ("Work package review", [packages[key]["reviews"] for key in needs], "fail"),
                    ("Design review", [module["design_history"] for module in modules
                                       if module["id"] in cone_modules], "changes"),
                )
                for reviews in rows for review in reviews
                if review["verdict"] == verdict and timestamp and
                ((baseline or timestamp) if kind == "Design review" else "") <= (review.get("at") or "") <= timestamp
            )
            retro = dict(first=min(starts, default=None), cost=total_known(run["cost"] for run in runs),
                         priced=sum(run["cost"] is not None for run in runs), sessions=len(runs),
                         failed_by_module=dict(failures + design_changes),
                         failed_by_task={"work package review": sum(failures.values()),
                                         "design review": sum(design_changes.values())},
                         review_hosts=[dict(task=kind, host=host, count=count)
                                       for (kind, host), count in sorted(review_hosts.items())],
                         baseline=baseline, planned=sum(date <= baseline for date in dates) if baseline else None,
                         added=[key for key in needs if baseline and introduced.get(key, "") > baseline])
        result.append(dict(label=label, ref="milestone/" + label, name=name, about=about,
                           closed_by=closer, needs=needs, done=len(needs) - len(left), total=len(needs), left=left,
                           longest_chain=max((chain(key) for key in left), key=len, default=[]),
                           closed_at=closure or (timestamp if needs and not left else None),
                           closed=bool(closure or needs and not left), historical=bool(closure and not closer), retro=retro))
    return result


def annotate_dependencies(modules, packages, milestones, needs_you, pace, sessions, snapshot):
    forward = {key: set(wp["needed_by"]) for key, wp in packages.items()}
    for module in modules:
        for before, after in pairwise(module["work_packages"]):
            forward[before].add(after)

    def downstream(key):
        pending, found = list(forward[key]), set()
        while pending:
            following = pending.pop()
            if following == key or following in found or packages[following]["status"] == "done":
                continue
            found.add(following)
            pending.extend(forward[following])
        return found

    for question in needs_you:
        key = question.get("ref")
        if not key:
            continue
        held = downstream(key)
        question["holds"] = dict(count=len(held), modules=sorted({packages[p]["module"] for p in held}),
                                 milestones=[m["label"] for m in milestones if key in m["left"]])
        for wp in held:
            packages[wp].setdefault("held_by", []).append(key)
    needs_you.sort(key=lambda q: (len(q.get("holds", {}).get("milestones", [])),
                                  q.get("holds", {}).get("count", 0)), reverse=True)

    week = pace[-8:-1]
    throughput = sum(day["done"] for day in week) / len(week)
    recent_durations = [
        (instant(s["end"]) - instant(s["start"])).total_seconds() / 86400
        for s in sessions if s["kind"] == "builder" and s["end"] and
        snapshot - timedelta(days=7) <= instant(s["end"]) <= snapshot
    ]
    stretch = median(recent_durations) if recent_durations else 0
    for milestone in milestones:
        chain = milestone["longest_chain"]
        if not chain:
            continue
        user_blocks = list(dict.fromkeys(
            block for key in chain for block in
            ([key] if (packages[key]["waiting"] or {}).get("on") == "user" else packages[key].get("held_by", []))
        ))
        milestone["held_by"] = user_blocks
        if not user_blocks and throughput:
            days = max(len(milestone["left"]) / throughput, len(chain) * stretch)
            milestone["expected_at"] = iso(snapshot + timedelta(days=days))

    for wp in packages.values():
        waiting = wp["waiting"] or {}
        if waiting.get("on") != "dependency":
            continue
        refs = re.findall(r"([A-Z0-9_.-]+:(?:WP|U)\d+)", waiting.get("detail") or "")
        waiting["targets"] = list(dict.fromkeys(
            dep for dep in (refs or wp["depends_on"]) if dep in packages and packages[dep]["status"] != "done"
        ))


def package_warnings(flow, packages):
    warnings = defaultdict(list)
    phrases = {
        "same_builder": "the next try stays with the same builder",
        "new_builder_session": "the next try uses a fresh builder",
    }
    for line in [*flow.get("warning_signs", []), *flow.get("back_and_forth", [])]:
        match = re.search(r"\b([A-Z][A-Z0-9-]+)[ :](WP\d+|U\d+)\b", line)
        key = ":".join(match.groups()) if match else None
        if not key or key not in packages:
            warnings[None].append(line.rstrip(".") + ".")
            continue
        sentence = (line[:match.start()] + line[match.end():]).strip(" :;,")
        sentence = re.sub(r"the counts now call for (\w+)",
                          lambda m: phrases.get(m[1], "the next try needs a decision"), sentence)
        sentence = sentence[:1].upper() + sentence[1:].rstrip(".").replace("; the next try", ". The next try") + "."
        if sentence not in warnings[key]:
            warnings[key].append(sentence)
    return [dict(ref=key, text=" ".join(lines)) for key, lines in warnings.items()]


def build(root, prof, flow, dash, *, module_table, module_stems, live_runs, content, here, recorded_done,
          supervisor_running):
    plans = Path(prof["plans"])

    def read_text(path):
        try:
            with content.open(str(path)) as handle:
                return handle.read().decode(errors="replace")
        except OSError:
            return ""

    def read_json(path):
        data = json.loads(read_text(path) or "{}")
        return data if isinstance(data, dict) else {}

    def evidence(value):
        return dict(path=value, here=content.locate(value) is not None)

    vision = read_text(plans / "VISION.md")
    name = dash.get("meta", {}).get("project") or root.name
    title = re.match(r"# Vision and scope document for (.+)", vision, re.IGNORECASE)
    if title:
        name = title[1].strip()
    request = section(vision, r"the request|goal|the goal")
    quoted = re.search(r"^>[^\n]*(?:\n>[^\n]*)*", request, re.MULTILINE)
    goal = " ".join(re.sub(r"(?m)^>\s?", "", quoted[0] if quoted else request).split())
    architecture = read_text(plans / "ARCHITECTURE.md")
    status = read_text(plans / "STATUS.md")
    generated = dash.get("meta", {}).get("generated")
    snapshot = instant(generated) if generated else datetime.now(timezone.utc)
    head = git(root, "rev-parse", "--verify", "HEAD").strip()
    plan_changes, introduced = file_history(root, plans, head)
    sessions, costs = sessions_from(dash)
    runs_by_wp = defaultdict(list)
    for run in sessions:
        if run["kind"] == "builder":
            runs_by_wp[run["ref"]].append(run)

    events = {}
    state_events = {}
    event_results = {"READY_FOR_REVIEW": "ready_for_review", "BLOCKED": "blocked"}
    package_index = {ref(item["module"], item["work_package"]): item for item in dash.get("work_packages", [])}

    def event(date, kind, key, text, **extra):
        if date:
            date = iso(instant(date))
            events.setdefault((date, kind, key, extra.get("commit")), dict(at=date, kind=kind, ref=key, text=text, **extra))

    dashboard_transitions = []
    for entry in dash.get("events", []):
        key = ref(entry.get("module"), entry.get("work_package"))
        kind = event_results.get(entry.get("result"))
        if key and kind:
            state_events[key, kind] = max(entry["at"], state_events.get((key, kind), ""))
            dashboard_transitions.append((entry, kind, key))

    for change in plan_changes:
        match = re.match(r"orchestrate: ([A-Z0-9_.-]+) (WP\d+|M\d+|U\d+) blocked:", change["subject"])
        if match:
            state_events.setdefault((ref(*match.groups()), "blocked"), change["at"])

    waits = waiting_from(flow)
    running = []
    parents_with_steps = {run["steps_parent"] for run in live_runs if run.get("steps_parent")}
    for raw in live_runs:
        if raw.get("checks_only") or raw.get("waiting_for") or raw.get("pid") in parents_with_steps:
            continue
        module, wp = raw.get("module"), raw.get("work_package")
        role = raw.get("role")
        if role == "steps":
            role = {"run": "build", "plan": "plan"}.get(raw.get("origin"))
        kind = "design_review" if role == "review" and wp == "design" else ROLE.get(role)
        if kind:
            running.append(dict(kind=kind, ref=ref(module, wp), module=module.upper() if module else None,
                                start=iso(datetime.fromtimestamp(raw["started_at"], timezone.utc))
                                if raw.get("started_at") else None, end=None,
                                host=raw.get("host"), model=raw.get("model"), ended=None, cost=None))
    active = {run["ref"]: run["kind"] for run in running}

    choices_by_module = defaultdict(dict)
    for (module, choice), since in choices(root, plans / "STATUS.md",
                                            re.compile(r"^- ([A-Z0-9-]+) assumes:\s*(.+)"), status):
        choice = re.sub(r"\s+\(\[plan\]\([^)]+\)\)$", "", choice)
        choices_by_module[module][choice] = since

    needs_you = []
    for line in re.split(r"^#{2,3} ", status, flags=re.M):
        if line.startswith("Needs you now\n"):
            needs_you.extend(dict(ref=None, detail=match) for match in re.findall(r"^- (.+)", line, re.M)
                             if match.rstrip(".").lower() != "nothing")

    modules, packages, documents = [], {}, {}
    listed = {row["module"].upper(): row for row in module_table(architecture) or []}
    stems = {stem.upper(): stem for stem in module_stems}
    for order, module in enumerate(dict.fromkeys([*listed, *stems]), 1):
        delivers = listed.get(module, {}).get("what", "")
        base = plans / stems.get(module, listed.get(module, {}).get("module", module))
        if base.parent != plans:
            continue
        done = read_json(base / "DONE.json")
        record = read_json(base / "RECORD.json")
        design = (record.get("design") or {}).get("verdict")
        design_state = "approved" if design == "ok" else "not_approved"
        design_time = at(record.get("design"))
        if (not design_time or instant(design_time) <= snapshot) and any(
            line == f"{module}: design not approved" for line in flow.get("not_moving", [])
        ):
            design_state = "not_approved"
        if any(run["module"] == module and run["kind"] == "design_review" for run in running):
            design_state = "in_review"

        picked = {}
        choices_pattern = re.compile(r"^\s*(?:-\s*)?(?:Assumption:|assumes:?)\s+(.+)", re.I)
        for (choice,), since in choices(root, base / "PLAN.md", choices_pattern, read_text(base / "PLAN.md")):
            picked[choice] = since
        for choice, since in choices_by_module[module].items():
            if not any(existing.startswith(choice) or choice.startswith(existing) for existing in picked):
                picked[choice] = since
        links = {}
        for doc in ("design", "plan", "log"):
            path = base / f"{doc.upper()}.md"
            if document := read_text(path):
                links[doc] = f"#/doc/{module}/{doc}"
                documents[f"{module}/{doc}"] = {"path": str(path)}
                if doc == "log":
                    entries = re.split(r"\n(?=- |## )", document.strip())
                    entries = [entry for entry in entries if not entry.startswith("# ")]
                    documents[f"{module}/{doc}"]["excerpt"] = "\n".join(entries[-3:][::-1])[:1800]
        work_keys = []
        for row in done.get("work_packages", []):
            wp_id = row["id"]
            key = ref(module, wp_id)
            if not key:
                continue
            work_keys.append(key)
            saved = package_index.get(key, {})
            rec = record.get("work_packages", {}).get(wp_id, {})
            reviews, items = [], []
            for number, review in enumerate(rec.get("reviews", []), 1):
                usage = review.get("usage", {})
                tokens = total_known(usage.get(field) for field in ("input", "output"))
                path = review.get("review")
                reviews.append(dict(n=number, at=review.get("at"), verdict=review["verdict"], summary=review.get("summary"),
                                    host=review.get("host"), model=review.get("model"), findings=review.get("findings", []),
                                    tokens=tokens, text=path, text_here=bool(path and evidence(path)["here"])))
                if review["verdict"] == "fail":
                    event(review.get("at"), "review_failed", key, None)
            for item in row["items"]:
                value = item.get("evidence") or []
                paths = [value] if isinstance(value, str) else value
                proof = dict(id=item["id"], statement=item["statement"],
                             verdicts=[r.get("items", {}).get(item["id"]) for r in rec.get("reviews", [])])
                proof.update({field: item[field] for field in ("check", "inspect", "ask", "verdict")
                              if item.get(field)})
                if paths:
                    proof["evidence"] = [evidence(p) for p in paths]
                items.append(proof)
            state = row.get("status") or saved.get("status") or "not_started"
            if state == "done" and record and not recorded_done(row, record):
                state = "in_progress"
            wait = waits.get(key)
            blocked = row.get("blocked", {})
            if state == "blocked":
                reason = blocked.get("reason")
                detail = blocked.get("what") or (wait or {}).get("detail")
                since = state_events.get((key, "blocked"))
                wait = dict(on="user" if reason in USER_REASONS else (wait or {}).get("on", "failure"),
                            detail=detail, since=since, reason=reason)
                event(since, "blocked", key, detail)
                if wait["on"] == "user":
                    action = flow.get("actions", {}).get(key.replace(":", " "), {})
                    needs_you.append(dict(ref=key, detail=action.get("ask") or detail, reason=reason))
            elif key in active and state != "done":
                state = {"reviewer": "reviewing", "builder": "building"}.get(active[key], state)
                wait = dict(on="none", detail=None, since=next(run["start"] for run in running if run["ref"] == key))
            elif wait and wait["on"] == "dependency" and state == "not_started":
                state = "waiting"
            elif state == "not_started" and wait and "ready to build" in wait["detail"]:
                state = "ready_to_build"
            elif state == "in_progress":
                state = "waiting"
                if not wait or wait["on"] == "user":
                    wait = dict(on="none", detail="No active run was found.", since=None)
            elif state == "ready_for_review" and (not wait or wait["on"] not in {"review", "merge", "lock", "failure"}):
                wait = dict(on="review", detail=None, since=None)
            if state in {"done", "not_started"}:
                wait = None
            elif wait is None:
                wait = dict(on="review" if state == "ready_for_review" else "none", detail=None, since=None)

            done_at = at(rec.get("done")) or saved.get("done")
            ready_at = at(rec.get("ready_for_review")) or saved.get("ready_for_review")
            event(done_at, "done", key, None)
            event(ready_at, "ready_for_review", key, None)
            started_at = min((run["start"] for run in runs_by_wp[key]), default=None)
            status_since = {"done": done_at, "ready_for_review": ready_at}.get(state)
            if wait:
                wait["since"] = wait["since"] or flow_age(wait["detail"] or "", snapshot) or status_since
                status_since = status_since or wait["since"]
            packages[key] = dict(module=module, id=wp_id, name=row["name"], status=state, waiting=wait,
                                 depends_on=[dep.upper() if ":" in dep else f"{module}:{dep.upper()}"
                                             for dep in row.get("depends_on") or []],
                                 needed_by=[], closes=row.get("closes"), items=items,
                                 reviews=reviews, done_at=done_at, started_at=started_at,
                                 status_since=status_since, failed_reviews=sum(r["verdict"] == "fail" for r in reviews),
                                 cost=total_known(run["cost"] for run in runs_by_wp[key]))
        modules.append(dict(id=module, name=module_name(module, read_text(base / "DESIGN.md")),
                            order=int(order), delivers=delivers.strip(), design=design_state,
                            waits_on=[], needed_by=[], work_packages=work_keys, links=links,
                            design_history=record.get("design_history", []),
                            choices=[dict(text=choice, since=since) for choice, since in picked.items()]))

    for key, row in packages.items():
        row["depends_on"] = [dep for dep in row["depends_on"] if dep in packages]
        for dep in row["depends_on"]:
            packages[dep]["needed_by"].append(key)
    for module in modules:
        rows = [packages[key] for key in module["work_packages"]]
        module["waits_on"] = list(dict.fromkeys(dep for row in rows for dep in row["depends_on"]
                                               if packages[dep]["module"] != module["id"]))
        module["needed_by"] = list(dict.fromkeys(dep for row in rows for dep in row["needed_by"]
                                                if packages[dep]["module"] != module["id"]))

    milestones = milestone_rows(vision, modules, packages, introduced, sessions)
    retro = {}
    for milestone in milestones:
        if detail := milestone.pop("retro"):
            retro[milestone["label"]] = detail
    for row in packages.values():
        del row["started_at"]
    for module in modules:
        module["design_history"] = [
            {key: review[key] for key in ("at", "verdict", "host", "model") if key in review}
            for review in module["design_history"]
        ]

    transitions = defaultdict(list)
    for entry in events.values():
        transitions[entry["kind"], entry["ref"]].append(instant(entry["at"]))
    for entry, kind, key in dashboard_transitions:
        date = instant(entry["at"])
        if not any(abs((date - recorded).total_seconds()) < 60 for recorded in transitions[kind, key]):
            event(entry["at"], kind, key, entry.get("detail") or None)
    for change in plan_changes:
        if change["definitions_changed"] or change["design_changed"] or change.get("files"):
            event(change["at"], "plan_changed", None, change["subject"], commit=change["commit"], modules=change["modules"])
    integration = integration_log(root, head)
    last_merge = None
    last_merge_ref = None
    for line in integration.splitlines():
        commit, date, parents, subject = line.split("\x1f", 3)
        match = re.match(r"orchestrate: review of ([A-Z0-9_.-]+) (WP\d+|M\d+|U\d+): PASS\b", subject)
        if len(parents.split()) > 1 or match:
            key = ref(*match.groups()) if match else None
            if last_merge is None:
                last_merge = iso(instant(date))
                last_merge_ref = key
            event(date, "merged", key, subject, commit=commit)

    days = {(snapshot.date() - timedelta(days=delta)).isoformat(): dict(done=0, passed=0, reviews=0)
            for delta in reversed(range(14))}
    for package in packages.values():
        if (date := (package["done_at"] or "")[:10]) in days:
            days[date]["done"] += 1
        for review in package["reviews"]:
            if (date := (review["at"] or "")[:10]) in days:
                days[date]["reviews"] += 1
                days[date]["passed"] += review["verdict"] == "pass"
    pace = [dict(day=day, **row, pass_rate=row["passed"] / row["reviews"] if row["reviews"] else None)
            for day, row in days.items()]
    annotate_dependencies(modules, packages, milestones, needs_you, pace, sessions, snapshot)
    warnings = package_warnings(flow, packages)
    vision_exit = re.search(r"\*\*V1 exit:\*\*\s*([^\n]+(?:\n(?!\s*$|#|[-*]>)[^\n]+)*)", vision)
    error_kinds = {"turn_timed_out", "turn_aborted", "turn_failed", "script_refused"}
    errors = [dict(kind=e.get("class") or e["kind"], at=e["at"], session=e.get("session"))
              for e in dash.get("events", []) if e["kind"] in error_kinds]
    error_ids = {e["session"] for e in errors if e["session"]}
    error_sessions = {s["session"]: {k: s[k] for k in ("start", "end", "host", "model", "module", "work_package", "role")
                                      if k in s} for s in dash.get("sessions", []) if s["session"] in error_ids}

    state = ("running" if running or supervisor_running else "paused") if here["run_state"] else None
    events = sorted(events.values(), key=lambda entry: entry["at"], reverse=True)
    model = dict(
        project=dict(name=name, goal=goal, built_at=iso(datetime.now(timezone.utc)), snapshot_at=iso(snapshot),
                     script_version=dash.get("meta", {}).get("version"), state=state, vision=vision,
                     v1_exit=" ".join(vision_exit[1].split()) if vision_exit else
                     section(vision, r"first release|what finishes this goal"),
                     open_decisions=section(vision, "still open"),
                     source_root=str(root), plan_commit=head, here=here,
                     plans=plans.as_posix(), evidence=prof["evidence"]),
        milestones=milestones, modules=modules, work_packages=packages, documents=documents,
        now=dict(running=running, builders=flow.get("builders", {}),
                 reviews_running=sum(run["kind"] in {"reviewer", "design_review"} for run in running),
                 last_merge=last_merge, last_merge_ref=last_merge_ref,
                 supervisor=("running" if supervisor_running else "stopped") if here["run_state"] else None,
                 needs_you=needs_you, warnings=warnings,
                 recent_events=events[:50], event_times=[(int(instant(e["at"]).timestamp()), e["kind"]) for e in events]),
        plan_changes=[c for c in plan_changes if c["definitions_changed"] or c["design_changed"] or c.get("files")],
        plan_commit_count=len(plan_changes),
        pace=pace,
    )
    history = dict(
        sessions=sessions, events=events, checks=dash.get("checks", []), retro=retro,
        agents=agents_summary(dash, snapshot) if here["history"] else None,
        machinery=dict(machine=flow.get("machine"), quota=flow.get("quota"), main_branch=flow.get("main_branch"),
                       locks=flow.get("flow", {}).get("locks"), merges=flow.get("flow", {}).get("merges"),
                       checks=flow.get("flow", {}).get("checks"), costs=sorted(costs, key=lambda row: row["cost"] or 0, reverse=True),
                       errors=errors, error_sessions=error_sessions,
                       check_outcomes=dict(Counter("passed" if check["exit"] == 0 else "failed"
                                                   for check in dash.get("checks", [])))),
    )
    return model, history, plan_changes


@lru_cache(maxsize=4)
def integration_log(root, head):
    # A fast-forwarded review still records a merge in delivery's commit history.
    return git(root, "log", "--first-parent", "--format=%H%x1f%cI%x1f%P%x1f%s", head) if head else ""


def agents_summary(dash, snapshot):
    """What the old dashboard drew, reduced to the figures the Agents section shows: per kind of agent, per day,
    per model and per script version, plus turn lengths, context fill and why turns ended badly."""
    if not dash:
        return None
    session_kinds = {"interactive": "lead", "subagent": "subagent", "auto-review": "approval reviewer", "script": "script"}
    role_kinds = {"build": "builder", "review": "reviewer", "plan": "planner"}
    sessions = dash.get("sessions", [])
    turns = [dict(zip(dash["turns"]["columns"], values)) for values in dash.get("turns", {}).get("rows", [])]
    for turn in turns:
        kind = sessions[turn["s"]]["kind"] if turn["s"] is not None and turn["s"] < len(sessions) else None
        turn["kind"] = role_kinds.get(turn["role"]) or session_kinds.get(kind, "other")
    first_day = (snapshot - timedelta(days=13)).date()
    days = [(first_day + timedelta(days=i)).isoformat() for i in range(14)]

    def quantile(values, q):
        values = sorted(v for v in values if v is not None)
        return values[min(len(values) - 1, int(q * len(values)))] if values else None

    def fill(turn):
        return turn["peak_context"] / turn["window"] if turn["peak_context"] and turn["window"] else None

    kinds = []
    for kind, rows in groupby_key(turns, "kind").items():
        kinds.append(dict(kind=kind, sessions=len({r["s"] for r in rows}), turns=len(rows),
                          median_s=round((quantile([r["duration_ms"] for r in rows], .5) or 0) / 1000),
                          p90_s=round((quantile([r["duration_ms"] for r in rows], .9) or 0) / 1000),
                          weighted=sum(r["weighted"] or 0 for r in rows), usd=round(sum(r["usd"] or 0 for r in rows), 2),
                          priced=sum(1 for r in rows if r["usd"]), aborted=sum(r["ended"] == "aborted" for r in rows),
                          context_p90=quantile([fill(r) for r in rows], .9)))
    kinds.sort(key=lambda row: row["weighted"], reverse=True)

    daily = {day: dict(day=day, weighted={}, usd=0.0, errors=0, turns=0) for day in days}
    for turn in turns:
        row = daily.get((turn["start"] or "")[:10])
        if row:
            row["weighted"][turn["kind"]] = row["weighted"].get(turn["kind"], 0) + (turn["weighted"] or 0)
            row["usd"] = round(row["usd"] + (turn["usd"] or 0), 2)
            row["turns"] += 1
    error_kinds = {"turn_timed_out": "Timed out", "turn_aborted": "Aborted", "turn_stopped": "Stopped",
                   "turn_failed": "Failed", "script_refused": "Script refused", "goal_limited": "Goal limit reached"}
    failures = Counter()
    for event in dash.get("events", []):
        if event["kind"] in error_kinds:
            failures[error_kinds[event["kind"]]] += 1
            row = daily.get(event["at"][:10])
            if row:
                row["errors"] += 1
    limit = [dict(at=e["at"], used=e["used_percent"]) for e in dash.get("events", [])
             if e["kind"] == "limit_changed" and e.get("limit") == "primary" and e["at"][:10] >= days[0]]
    limit = limit[::max(1, len(limit) // 160)]

    models = []
    for name, rows in groupby_key([t for t in turns if t["model"] and " " not in t["model"].strip()], "model").items():
        models.append(dict(model=name, turns=len(rows), weighted=sum(r["weighted"] or 0 for r in rows),
                           usd=round(sum(r["usd"] or 0 for r in rows), 2)))
    models.sort(key=lambda row: row["weighted"], reverse=True)

    versions = []
    for name, rows in groupby_key([t for t in turns if t["version"]], "version").items():
        versions.append(dict(version=name, first=min(r["start"] for r in rows), turns=len(rows),
                             aborted=sum(r["ended"] == "aborted" for r in rows),
                             median_s=round((quantile([r["duration_ms"] for r in rows], .5) or 0) / 1000)))
    versions.sort(key=lambda row: row["first"], reverse=True)

    edges = [(10, "under 10s"), (60, "10s–1m"), (300, "1–5m"), (900, "5–15m"), (3600, "15m–1h"), (None, "over 1h")]
    durations = Counter()
    for turn in turns:
        seconds = (turn["duration_ms"] or 0) / 1000
        durations[next(label for edge, label in edges if edge is None or seconds < edge)] += 1
    context_edges = [(.25, "under 25%"), (.5, "25–50%"), (.75, "50–75%"), (.9, "75–90%"), (None, "over 90%")]
    context = Counter()
    for turn in turns:
        share = fill(turn)
        if share is not None and turn["kind"] in {"builder", "reviewer", "planner", "lead"}:
            context[next(label for edge, label in context_edges if edge is None or share < edge)] += 1
    return dict(kinds=kinds, daily=list(daily.values()), failures=failures.most_common(), limit=limit,
                models=models[:8], versions=versions[:12], token_order=dash.get("meta", {}).get("token_order"),
                durations=[(label, durations[label]) for _, label in edges],
                context=[(label, context[label]) for _, label in context_edges],
                totals=dict(sessions=len(sessions), turns=len(turns), weighted=sum(t["weighted"] or 0 for t in turns),
                            usd=round(sum(t["usd"] or 0 for t in turns), 2), priced=sum(1 for t in turns if t["usd"])))


def groupby_key(rows, key):
    groups = {}
    for row in rows:
        groups.setdefault(row[key], []).append(row)
    return groups
