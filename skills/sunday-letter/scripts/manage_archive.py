#!/usr/bin/env python3
"""Build and serve the private local Sunday Letter archive."""

from __future__ import annotations

import argparse
import mimetypes
import shutil
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from core import atomic_write_text, ensure_private_directory, load_ledger, save_ledger, text


DEFAULT_ROOT = Path.home() / "sunday-letter"


ARCHIVE_CSS = """
:root { --paper:#eeeae0; --card:#f8f5ec; --ink:#1a1a1a; --muted:#6b6b6b; --green:#1a4c2e; --rule:rgba(26,26,26,.12); }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
.shell { width:min(920px,calc(100% - 32px)); margin:0 auto; padding:52px 0 80px; }
.eyebrow,.meta { font:11px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }
h1 { margin:10px 0 8px; font-size:clamp(36px,7vw,64px); letter-spacing:-.045em; }
.lede { max-width:650px; color:#3a3a38; font-size:17px; line-height:1.6; }
.toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:30px 0; padding:18px; border:1px solid var(--rule); border-radius:10px; background:rgba(255,255,255,.25); }
button,.button { appearance:none; border:1px solid var(--ink); border-radius:6px; padding:9px 13px; background:var(--ink); color:white; font:600 12px/1 Inter,sans-serif; text-decoration:none; cursor:pointer; }
button.secondary,.button.secondary { background:transparent; color:var(--ink); border-color:var(--rule); }
.status { margin-left:auto; color:var(--green); font:600 12px/1 ui-monospace,monospace; text-transform:uppercase; }
.timeline { list-style:none; margin:0; padding:0; border-top:1px solid var(--rule); }
.entry { display:grid; grid-template-columns:125px 1fr auto; gap:22px; align-items:start; padding:22px 0; border-bottom:1px solid var(--rule); }
.entry h2 { margin:0 0 6px; font-size:20px; letter-spacing:-.02em; }
.entry p { margin:0; color:var(--muted); line-height:1.5; }
.entry a { color:var(--ink); }
.silent h2 { font-style:italic; color:var(--muted); }
.actions { display:flex; gap:8px; align-items:center; }
.empty { padding:44px 0; color:var(--muted); }
.local-note { margin-top:28px; padding-top:18px; border-top:1px solid var(--rule); color:var(--muted); font-size:13px; line-height:1.5; }
form { margin:0; }
@media(max-width:650px) { .shell{padding-top:30px}.entry{grid-template-columns:1fr;gap:8px}.status{width:100%;margin:4px 0 0}.actions{justify-content:flex-start} }
"""


def _ledger_path(root: Path) -> Path:
    return root.expanduser().resolve() / "ledger.json"


def build_archive(root: Path) -> Path:
    root = root.expanduser().resolve()
    ensure_private_directory(root)
    ledger = load_ledger(_ledger_path(root))
    entries: list[str] = []
    events = list(ledger["events"])
    files_in_events = {event.get("file") for event in events if event.get("file")}
    events.extend(
        letter for letter in ledger["letters"] if letter.get("file") not in files_in_events
    )
    for event in reversed(events):
        if event.get("status") == "skipped":
            entries.append(
                f"""
        <li class="entry silent">
          <div class="meta">{text(event.get('date'))}</div>
          <div><h2>Silent this week</h2><p>{text(event.get('reason'))}</p></div>
          <div class="meta">Skipped</div>
        </li>"""
            )
            continue
        raw_file_value = str(event.get("file") or "")
        raw_signals_file = str(event.get("signals_file") or "")
        if not raw_file_value:
            continue
        try:
            file_value = _safe_letter_path(root, raw_file_value).relative_to(root).as_posix()
        except ValueError:
            continue
        signals_file = ""
        if raw_signals_file:
            try:
                signals_file = _safe_letter_path(root, raw_signals_file).relative_to(root).as_posix()
            except ValueError:
                pass
        signals_link = (
            f'<a class="button secondary" href="{text(signals_file)}" download>Signals</a>'
            if signals_file
            else ""
        )
        entries.append(
            f"""
        <li class="entry">
          <div class="meta">{text(event.get('date'))} · №{text(event.get('number'))}</div>
          <div>
            <h2><a href="{text(file_value)}">{text(event.get('headline'), 'Untitled letter')}</a></h2>
            <p>A grounded note from the selected local Codex sources.</p>
          </div>
          <div class="actions">
            <a class="button secondary" href="{text(file_value)}" download>Export</a>
            {signals_link}
            <form method="post" action="/action/delete">
              <input type="hidden" name="file" value="{text(file_value)}">
              <button class="secondary" type="submit">Delete</button>
            </form>
          </div>
        </li>"""
        )

    if not entries:
        entries.append('<li class="empty">No letters yet. A silent week is a valid first entry.</li>')
    paused = bool(ledger.get("paused"))
    pause_action = "resume" if paused else "pause"
    pause_label = "Resume" if paused else "Pause"
    status = "Paused" if paused else "Active"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'">
<title>The Sunday Letter · Local archive</title>
<style>{ARCHIVE_CSS}</style>
</head>
<body>
<main class="shell">
  <div class="eyebrow">Private local archive · Codex</div>
  <h1>The Sunday Letter</h1>
  <p class="lede">A running record of shipped letters and intentional silence. This page is generated from <code>ledger.json</code> and files under <code>letters/</code>.</p>
  <div class="toolbar">
    <form method="post" action="/action/{pause_action}"><button type="submit">{pause_label}</button></form>
    <a class="button secondary" href="/export.zip">Export archive</a>
    <a class="button secondary" href="/">Refresh</a>
    <span class="status">{status}</span>
  </div>
  <ol class="timeline">{''.join(entries)}</ol>
  <p class="local-note">Pause, Delete, and full-archive Export work through the local server: <code>python3 manage_archive.py serve</code>. Letter and per-letter Export links remain usable when this page is opened directly as a file.</p>
</main>
</body>
</html>
"""
    index = root / "index.html"
    atomic_write_text(index, html)
    return index


def set_paused(root: Path, paused: bool) -> None:
    root = root.expanduser().resolve()
    ledger = load_ledger(_ledger_path(root))
    ledger["paused"] = paused
    save_ledger(_ledger_path(root), ledger)
    build_archive(root)


def archive_status(root: Path) -> str:
    ledger = load_ledger(_ledger_path(root))
    state = "paused" if ledger.get("paused") else "active"
    return (
        f"{state}; letters={len(ledger['letters'])}; last_number={ledger['letter_number']}; "
        f"last_status={ledger.get('last_status') or 'never run'}"
    )


def _safe_letter_path(root: Path, file_value: str) -> Path:
    root = root.expanduser().resolve()
    letters_root = (root / "letters").resolve()
    candidate = (root / file_value).resolve()
    try:
        candidate.relative_to(letters_root)
    except ValueError as error:
        raise ValueError("letter path must stay inside the archive letters directory") from error
    return candidate


def delete_letter(root: Path, file_value: str) -> None:
    root = root.expanduser().resolve()
    target = _safe_letter_path(root, file_value)
    target.unlink(missing_ok=True)
    ledger = load_ledger(_ledger_path(root))
    def matches(item: dict[str, object]) -> bool:
        try:
            return _safe_letter_path(root, str(item.get("file") or "")) == target
        except ValueError:
            return False

    matching = next((item for item in ledger["letters"] if matches(item)), None)
    if matching and matching.get("signals_file"):
        try:
            _safe_letter_path(root, str(matching["signals_file"])).unlink(missing_ok=True)
        except ValueError:
            pass
    ledger["letters"] = [item for item in ledger["letters"] if not matches(item)]
    ledger["events"] = [item for item in ledger["events"] if not matches(item)]
    save_ledger(_ledger_path(root), ledger)
    build_archive(root)


def export_archive(root: Path, out_path: Path) -> Path:
    root = root.expanduser().resolve()
    out_path = out_path.expanduser().resolve()
    build_archive(root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_path, "w", ZIP_DEFLATED) as archive:
        for relative in (Path("ledger.json"), Path("index.html")):
            path = root / relative
            if path.exists():
                archive.write(path, relative.as_posix())
        letters = root / "letters"
        if letters.exists():
            for path in sorted(letters.iterdir()):
                if not path.is_file() or path.suffix not in {".html", ".json"}:
                    continue
                archive.write(path, path.relative_to(root).as_posix())
    out_path.chmod(0o600)
    return out_path


def _handler(root: Path) -> type[BaseHTTPRequestHandler]:
    class ArchiveHandler(BaseHTTPRequestHandler):
        def _redirect_home(self) -> None:
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.end_headers()

        def _serve_file(self, path: Path, content_type: str | None = None) -> None:
            if not path.exists() or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(path.stat().st_size))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with path.open("rb") as source:
                shutil.copyfileobj(source, self.wfile)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._serve_file(build_archive(root), "text/html; charset=utf-8")
                return
            if parsed.path == "/export.zip":
                exported = export_archive(root, root / "sunday-letter-export.zip")
                self._serve_file(exported, "application/zip")
                return
            if parsed.path.startswith("/letters/"):
                try:
                    target = _safe_letter_path(root, unquote(parsed.path.lstrip("/")))
                except ValueError:
                    self.send_error(HTTPStatus.BAD_REQUEST)
                    return
                self._serve_file(target)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            origin = self.headers.get("Origin")
            expected_origin = f"http://{self.headers.get('Host', '')}"
            if origin and origin != expected_origin:
                self.send_error(HTTPStatus.FORBIDDEN, "cross-origin archive action blocked")
                return
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                self.send_error(HTTPStatus.FORBIDDEN, "cross-site archive action blocked")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "invalid content length")
                return
            if length < 0 or length > 65_536:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return
            values = parse_qs(self.rfile.read(length).decode("utf-8"))
            try:
                if self.path == "/action/pause":
                    set_paused(root, True)
                elif self.path == "/action/resume":
                    set_paused(root, False)
                elif self.path == "/action/delete":
                    file_value = values.get("file", [""])[0]
                    delete_letter(root, file_value)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
            except (ValueError, OSError) as error:
                self.send_error(HTTPStatus.BAD_REQUEST, str(error))
                return
            self._redirect_home()

        def log_message(self, format_value: str, *args: object) -> None:
            print(f"archive: {format_value % args}")

    return ArchiveHandler


def serve_archive(root: Path, host: str, port: int) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("archive server host must be 127.0.0.1 or localhost")
    root = root.expanduser().resolve()
    build_archive(root)
    server = ThreadingHTTPServer((host, port), _handler(root))
    print(f"Serving the private Sunday Letter archive at http://{host}:{port}/")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the private local Sunday Letter archive.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("build")
    subparsers.add_parser("pause")
    subparsers.add_parser("resume")
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--out", type=Path)
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("file")
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.command == "status":
        print(archive_status(args.root))
    elif args.command == "build":
        print(build_archive(args.root))
    elif args.command == "pause":
        set_paused(args.root, True)
        print("Sunday Letter paused.")
    elif args.command == "resume":
        set_paused(args.root, False)
        print("Sunday Letter resumed.")
    elif args.command == "export":
        out = args.out or args.root.expanduser() / "sunday-letter-export.zip"
        print(export_archive(args.root, out))
    elif args.command == "delete":
        delete_letter(args.root, args.file)
        print(f"Deleted {args.file}.")
    elif args.command == "serve":
        if args.host not in {"127.0.0.1", "localhost"}:
            parser.error("archive server host must be 127.0.0.1 or localhost")
        serve_archive(args.root, args.host, args.port)


if __name__ == "__main__":
    main()
