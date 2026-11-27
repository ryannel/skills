"""The loopback HTTP server for the observability page."""
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import shutil
import stat
import sys
from threading import Condition, Event, Thread
from urllib.parse import unquote, urlsplit

POLL_SECONDS = 3
# A build rereads the same records `flow` does, which takes most of a minute on a large busy project, and a running
# project changes its records every few seconds. So a rebuild waits this long after the last one finished, which keeps
# the page within about a minute of the project without serve rebuilding all the time beside the builds it shows.
REBUILD_GAP_SECONDS = float(os.environ.get("ORCHESTRATE_SERVE_REBUILD_GAP", 30))  # the tests shorten it
HEARTBEAT_SECONDS = 15
PAGE = Path(__file__).with_name("observability.html")
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/avif"}


def relative_path(value):
    if not isinstance(value, str) or "\0" in value or "\\" in value:
        return None
    path = Path(value)
    return path if path.parts and not path.is_absolute() and ".." not in path.parts else None


@dataclass(frozen=True)
class Content:
    root: Path
    common: Path
    plans: str
    evidence: str

    def folders(self):
        if (prefix := relative_path(self.plans)):
            target = self.root / prefix
            if target.resolve() == target and not target.is_relative_to(self.common):
                yield prefix, target
        if (prefix := relative_path(self.evidence)):
            target = self.common / "orchestrate" / "evidence"
            # The usual checkout path is a link to this one shared working folder.
            # A real folder in a checkout can also hold evidence, including in a clone.
            if target.resolve() == target and target.is_dir():
                yield prefix, target
            else:
                local = self.root / prefix
                if local.resolve() == local and not local.is_relative_to(self.common):
                    yield prefix, local

    def locate(self, value):
        """Find a regular file below its configured folder, including the shared evidence folder."""
        try:
            relative = relative_path(value)
            if relative is None:
                return None
            for prefix, folder in self.folders():
                if relative == prefix or not relative.is_relative_to(prefix):
                    continue
                target = (folder / relative.relative_to(prefix)).resolve()
                if target.is_relative_to(folder) and target.is_file():
                    return folder, target.relative_to(folder)
        except (OSError, RuntimeError, ValueError):
            pass
        return None

    def open(self, value):
        found = self.locate(value)
        if found is None:
            raise FileNotFoundError(value)
        folder, path = found
        # Walk the resolved path using open directories. Refuse a symlink swapped in after the containment check.
        flags = os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(folder.anchor, flags)
        try:
            for part in (*folder.parts[1:], *path.parts[:-1]):
                child = os.open(part, flags, dir_fd=fd)
                os.close(fd)
                fd = child
            handle = os.fdopen(os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd), "rb")
        finally:
            os.close(fd)
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            handle.close()
            raise FileNotFoundError(value)
        return handle


def source_times(files, trees):
    """An mtime signature with names, so atomic replacement, deletion and creation all count as changes."""
    times = {}

    def add(path):
        try:
            stamp = path.lstat()
            times[path] = (stamp.st_mtime_ns, stamp.st_size, stamp.st_ino)
        except FileNotFoundError:
            pass

    for path in files:
        add(path)
    for path in trees:
        add(path)
        for folder, _, names in os.walk(path):
            for name in names:
                add(Path(folder) / name)
    return times


class Server(ThreadingHTTPServer):
    def __init__(self, port, sources, build):
        super().__init__(("127.0.0.1", port), Handler)
        self.url = f"http://127.0.0.1:{self.server_port}/"
        self.page = PAGE.read_bytes()
        self.condition = Condition()
        self.stopping = Event()
        self.revision = 0
        self.sources, self.build = sources, build
        self.snapshot = None

    def refresh(self):
        content, model, history, commits = self.build()
        payloads = {f"/{name}.json": json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
                    for name, data in (("model", model), ("history", history), ("plan-commits", commits))}
        with self.condition:
            self.snapshot = content, payloads
            self.revision += 1
            self.condition.notify_all()

    def poll(self, previous):
        while not self.stopping.wait(POLL_SECONDS):
            try:
                current = self.sources()
                if current != previous:
                    self.refresh()
                    previous = current
                    if self.stopping.wait(REBUILD_GAP_SECONDS):
                        return
            except (Exception, SystemExit) as error:
                # Keep serving the last complete snapshot if a source is between writes. Retry on the next poll.
                print(f"serve: couldn't refresh: {error}", file=sys.stderr)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.send_error(403)
            return
        try:
            path = unquote(urlsplit(self.path).path, errors="strict")
        except (UnicodeError, ValueError):
            self.send_error(400)
            return
        content, payloads = self.server.snapshot
        try:
            if path in ("/", "/index.html"):
                self.reply(self.server.page, "text/html; charset=utf-8", page=True)
            elif path in payloads:
                self.reply(payloads[path], "application/json")
            elif path == "/events":
                self.events()
            elif path.startswith("/content/"):
                self.file(content, path.removeprefix("/content/"))
            else:
                self.send_error(404)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def headers_for(self, media, length=None):
        self.send_response(200)
        self.send_header("Content-Type", media)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if length is not None:
            self.send_header("Content-Length", str(length))

    def reply(self, body, media, page=False):
        self.headers_for(media, len(body))
        if page:
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
                             "base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def file(self, content, relative):
        try:
            handle = content.open(relative)
        except (OSError, ValueError):
            self.send_error(404)
            return
        with handle:
            guessed = mimetypes.guess_type(relative)[0]
            media = guessed if guessed in IMAGE_TYPES else "text/plain; charset=utf-8" if (
                Path(relative).suffix.lower() in {".md", ".json", ".log", ".txt", ".csv"}) else "application/octet-stream"
            self.headers_for(media, os.fstat(handle.fileno()).st_size)
            if media == "application/octet-stream":
                self.send_header("Content-Disposition", "attachment")
            self.end_headers()
            shutil.copyfileobj(handle, self.wfile)

    def events(self):
        server = self.server
        self.close_connection = True
        self.connection.settimeout(HEARTBEAT_SECONDS)
        # Capture the revision before sending headers, which can trigger the browser's first fetch.
        revision = server.revision
        self.headers_for("text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b": connected\n\n")
        self.wfile.flush()
        while not server.stopping.is_set():
            with server.condition:
                server.condition.wait_for(lambda: server.revision != revision or server.stopping.is_set(),
                                          HEARTBEAT_SECONDS)
                if server.stopping.is_set():
                    return
                changed = server.revision != revision
                revision = server.revision
            self.wfile.write(b"event: changed\ndata: {}\n\n" if changed else b": keepalive\n\n")
            self.wfile.flush()


def serve(port, sources, build, started):
    with Server(port, sources, build) as server:
        previous = sources()
        server.refresh()
        watcher = Thread(target=server.poll, args=(previous,), daemon=True)
        watcher.start()
        started(server.url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            with server.condition:
                server.stopping.set()
                server.condition.notify_all()
