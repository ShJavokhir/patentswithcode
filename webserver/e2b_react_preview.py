# e2b_react_preview.py
import sys
import time
from pathlib import Path
from e2b_code_interpreter import Sandbox
import os
import dotenv

dotenv.load_dotenv(".env.local")

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>E2B React Preview</title>
    <style>
      body {{
        margin: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #0f172a;
        color: #e5e7eb;
        display: flex;
        align-items: stretch;
        min-height: 100vh;
      }}
      #root {{
        flex: 1;
        padding: 24px;
      }}
      .banner {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        padding: 8px 16px;
        background: rgba(15, 23, 42, 0.95);
        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
        font-size: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 10;
      }}
      .banner span {{
        opacity: 0.7;
      }}
      .banner strong {{
        font-weight: 600;
      }}
    </style>

    <!-- React 18 + ReactDOM from CDN -->
    <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>

    <!-- Babel standalone so we can run JSX directly in the browser -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  </head>
  <body>
    <div class="banner">
      <span><strong>E2B React Preview</strong> – Rendering <code>App</code> from uploaded JSX</span>
      <span>Hot reload: re-run the Python script</span>
    </div>
    <div id="root" style="margin-top: 32px;"></div>

    <script type="text/babel">
{jsx_code}

      const rootElement = document.getElementById('root');
      if (typeof App === 'undefined') {{
        rootElement.innerHTML = "<pre style='color:#f97373'>Error: App component is not defined.\\n\\nMake sure your JSX file defines a global `App` component.</pre>";
      }} else {{
        const root = ReactDOM.createRoot(rootElement);
        root.render(React.createElement(App));
      }}
    </script>
  </body>
</html>
"""


def build_html_from_jsx(jsx_path: str) -> str:
    jsx_code = Path(jsx_path).read_text()
    indented_jsx = "\n".join("      " + line for line in jsx_code.splitlines())
    return HTML_TEMPLATE.format(jsx_code=indented_jsx)


def start_e2b_preview(jsx_path: str, port: int = 3000, timeout_seconds: int = 600):
    html = build_html_from_jsx(jsx_path)

    sbx = Sandbox.create(
      timeout=timeout_seconds,
    )

    # Write index.html into sandbox filesystem
    # use an absolute path, matching the docs style
    sbx.files.write("/home/user/index.html", html)

    # Start a simple HTTP server in the background
    sbx.commands.run(
        f"cd /home/user && python -m http.server {port}",
        background=True,
        timeout=5,  # just to start the process
    )

    # Give the server a moment to start
    time.sleep(2)

    # Get public host for this port
    host = sbx.get_host(port)
    url = f"https://{host}"

    print(f"\n✅ E2B React preview is live!")
    print(f"   JSX file: {jsx_path}")
    print(f"   URL: {url}\n")
    print("Keep this script running while you view the preview (Ctrl+C to stop).\n")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopping preview and killing sandbox...")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python e2b_react_preview.py path/to/App.jsx")
        sys.exit(1)

    jsx_file = sys.argv[1]
    if not Path(jsx_file).is_file():
        print(f"Error: file not found: {jsx_file}")
        sys.exit(1)

    start_e2b_preview(jsx_file)
