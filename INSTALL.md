# Research Tools - Installation Guide

MCP server za research u Claude Desktop. Omogućava pretragu dev.to, Google, Reddit i YouTube direktno iz Claude-a.

---

## Automatska instalacija (preporučeno)

Skripte automatski instaliraju sve potrebno (Python, uv) i konfigurišu Claude Desktop.

### Windows

1. Preuzmi [`install-windows.ps1`](https://raw.githubusercontent.com/halilc4/research-tools/main/scripts/install-windows.ps1)
2. Desni klik → "Run with PowerShell"
3. Prati uputstva (unesi API ključeve kad te pita)

Ili iz PowerShell-a:
```powershell
irm https://raw.githubusercontent.com/halilc4/research-tools/main/scripts/install-windows.ps1 | iex
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/halilc4/research-tools/main/scripts/install-macos.sh | bash
```

Skripta će:
- Instalirati Python i uv ako nedostaju
- Pitati te za API ključeve
- Konfigurisati Claude Desktop
- Restartovati Claude Desktop

---

## Manuelna instalacija

Ako prefiraš ručnu instalaciju ili automatska ne radi.

### Windows

#### 1. Instaliraj uv

Otvori **PowerShell** (desni klik na Start → Windows PowerShell) i zalepi:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Zatvori i ponovo otvori PowerShell, pa proveri instalaciju:

```powershell
uv --version
```

#### 2. Konfiguriši Claude Desktop

1. Otvori File Explorer i u address bar zalepi:
   ```
   %APPDATA%\Claude
   ```

2. Otvori fajl `claude_desktop_config.json` u Notepad-u (ako ne postoji, napravi ga)

3. Zalepi sledeći sadržaj:

```json
{
  "mcpServers": {
    "research-tools": {
      "command": "uvx",
      "args": ["--from", "mcp-cli-research-tools[mcp]", "rt-mcp"],
      "env": {
        "SERPER_API_KEY": "TVOJ_SERPER_KEY",
        "DEVTO_API_KEY": "TVOJ_DEVTO_KEY"
      }
    }
  }
}
```

4. Zameni `TVOJ_SERPER_KEY` i `TVOJ_DEVTO_KEY` sa pravim ključevima (pitaj Igora ako ih nemaš)

5. Sačuvaj fajl i restartuj Claude Desktop

### macOS

#### 1. Instaliraj uv

Otvori **Terminal** (Cmd+Space → ukucaj "Terminal") i zalepi:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Zatvori i ponovo otvori Terminal, pa proveri instalaciju:

```bash
uv --version
```

#### 2. Konfiguriši Claude Desktop

1. Otvori Terminal i zalepi:
   ```bash
   open ~/Library/Application\ Support/Claude/
   ```

2. Otvori fajl `claude_desktop_config.json` u TextEdit-u (ako ne postoji, napravi ga)

3. Zalepi sledeći sadržaj:

```json
{
  "mcpServers": {
    "research-tools": {
      "command": "uvx",
      "args": ["--from", "mcp-cli-research-tools[mcp]", "rt-mcp"],
      "env": {
        "SERPER_API_KEY": "TVOJ_SERPER_KEY",
        "DEVTO_API_KEY": "TVOJ_DEVTO_KEY"
      }
    }
  }
}
```

4. Zameni `TVOJ_SERPER_KEY` i `TVOJ_DEVTO_KEY` sa pravim ključevima

5. Sačuvaj fajl i restartuj Claude Desktop

---

## Provera

Nakon restarta Claude Desktop-a:

1. Klikni na ikonu čekića (🔨) u donjem desnom uglu
2. Trebalo bi da vidiš "research-tools" server
3. Probaj pitati Claude-a: "Nađi mi trending članke na dev.to o TypeScript-u"

---

## API Ključevi

| Servis | Gde dobiti |
|--------|------------|
| Serper | https://serper.dev/api-key |
| Dev.to | https://dev.to/settings/extensions |

Serper ima besplatan tier sa 2500 pretraga mesečno.
