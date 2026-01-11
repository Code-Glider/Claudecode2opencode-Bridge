# Dev Browser Service

Persistent browser automation server with LLM-friendly ARIA snapshots. Based on [SawyerHood/dev-browser](https://github.com/SawyerHood/dev-browser).

## Features

- **Persistent Pages**: Pages survive script restarts - maintain login state, cookies, localStorage
- **ARIA Snapshots**: Get LLM-friendly YAML representation of page structure with interactable refs
- **Named Pages**: Access pages by name from multiple scripts
- **Standard Playwright API**: Returns regular Playwright Page objects

## Quick Start

### 1. Install Dependencies

```bash
cd services/dev-browser
npm install
```

### 2. Start Server

```bash
./server.sh           # Visible browser
./server.sh --headless  # Headless mode
```

### 3. Use Python Client

```python
from services.dev_browser.client import DevBrowserClient

async with DevBrowserClient() as client:
    # Get or create a page
    page = await client.get_page("main")
    await page.goto("https://example.com")

    # Get LLM-friendly page structure
    snapshot = await client.get_ai_snapshot("main")
    print(snapshot)

    # Click element by ref
    element = await client.select_ref("main", "e5")
    await element.click()
```

## ARIA Snapshot Output

```yaml
- navigation [ref=e1]:
  - link "Home" [ref=e2]
  - link "Products" [ref=e3]
- main [ref=e4]:
  - heading "Welcome"
  - textbox "Search..." [ref=e5]
  - button "Submit" [ref=e6]
```

## API

### Python Client

```python
DevBrowserClient(
    server_url="http://localhost:9222",
    auto_start=True,    # Start server if not running
    headless=False,     # Headless mode for auto_start
    timeout=30.0        # Connection timeout
)
```

| Method | Description |
|--------|-------------|
| `get_page(name)` | Get or create named page |
| `list_pages()` | List all pages |
| `close_page(name)` | Close a page |
| `get_ai_snapshot(name)` | Get ARIA snapshot |
| `select_ref(page_name, ref)` | Get element by ref |

### HTTP API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info |
| `/pages` | GET | List pages |
| `/pages` | POST | Get/create page |
| `/pages/:name` | DELETE | Close page |

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `HEADLESS` | `false` | Headless mode |

## Ports

- `9222`: HTTP API
- `9223`: Chrome DevTools Protocol

## Troubleshooting

### Server won't start

```bash
# Check ports
lsof -i :9222
lsof -i :9223

# Kill stale processes
kill -9 $(lsof -ti:9222)
kill -9 $(lsof -ti:9223)

# Reinstall
rm -rf node_modules
npm install
npx playwright install chromium
```

### Stale refs

Refs become invalid after navigation. Always get a fresh snapshot after `goto()`.

## Files

```
services/dev-browser/
├── server.sh      # Launch script
├── client.py      # Python client
├── package.json   # Dependencies
├── src/           # TypeScript source
├── profiles/      # Persistent browser data
└── tmp/           # Temporary files
```

## License

MIT (original dev-browser by Sawyer Hood)
