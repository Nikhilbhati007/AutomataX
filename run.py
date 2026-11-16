"""Entry point runner for Automata Detective.

Starts the Uvicorn server and optionally opens the web dashboard in the default browser.
"""

from __future__ import annotations

import argparse
import sys
import webbrowser


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Automata Detective Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code change")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print("=" * 65)
    print("  AUTOMATA DETECTIVE: Learning & Visualizing DFAs from Data")
    print("=" * 65)
    print(f"  Starting local server at: {url}")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 65)

    if not args.no_browser:
        # Schedule browser opening after server launch
        import threading
        import time

        def _open():
            time.sleep(1.0)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    import uvicorn

    uvicorn.run("web.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
