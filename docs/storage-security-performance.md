# Storage, Security, and Performance

## Local database schema

Use SQLite for local history, prompt customization, settings, and provider health.

```sql
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  selected_text_hash TEXT NOT NULL,
  selected_text_preview TEXT NOT NULL,
  source_process TEXT,
  source_window_title TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  is_pinned INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_conversations_text_hash ON conversations(selected_text_hash);
CREATE INDEX idx_conversations_updated ON conversations(updated_at_utc);

CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  provider_id TEXT,
  model_id TEXT,
  created_at_utc TEXT NOT NULL,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);

CREATE TABLE prompt_actions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  template TEXT NOT NULL,
  icon TEXT,
  sort_order INTEGER NOT NULL,
  is_builtin INTEGER NOT NULL,
  is_enabled INTEGER NOT NULL DEFAULT 1,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE TABLE provider_health (
  provider_id TEXT PRIMARY KEY,
  last_success_utc TEXT,
  last_failure_utc TEXT,
  failure_count INTEGER NOT NULL DEFAULT 0,
  cooldown_until_utc TEXT,
  average_latency_ms INTEGER
);

CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE VIRTUAL TABLE conversation_search USING fts5(
  selected_text_preview,
  message_content,
  conversation_id UNINDEXED
);
```

## Local encryption

Encrypt:

- API keys.
- Sensitive settings.
- Optional conversation database.
- Export backups.

Recommended approach:

1. Store API keys in Windows Credential Manager.
2. Store other sensitive values with DPAPI `ProtectedData.Protect`.
3. Offer optional full-history encryption with a user passphrase for portability.

## Clipboard privacy

Rules:

- Clipboard fallback is last resort only.
- Snapshot clipboard temporarily in memory.
- Restore clipboard immediately.
- Do not write clipboard contents to logs, telemetry, crash dumps, or DB.
- Provide a setting to disable clipboard fallback.

## Sensitive mode

Sensitive mode should:

- Disable cloud calls unless explicitly approved.
- Prefer local models.
- Disable analytics.
- Disable clipboard fallback if configured.
- Avoid storing conversation history by default.
- Hide overlay in password and secure fields.

## Analytics

Analytics must be opt-in.

Allowed event examples:

- App startup duration.
- Overlay shown count.
- Provider latency bucket.
- Failure reason class.

Never collect:

- Selected text.
- Prompt text.
- Response content.
- Clipboard contents.
- API keys.
- Window titles unless user opts into diagnostics.

## Performance targets

| Metric | Target |
| --- | --- |
| Idle CPU | ~0% |
| Typical RAM | <150 MB |
| Hook callback time | <1 ms |
| Sidebar display after selection | <150 ms after debounce |
| Cold startup | <2 s |
| Clipboard fallback timeout | <600 ms |

## Performance optimizations

- Keep hook callbacks minimal and non-blocking.
- Debounce selection detection.
- Cache provider settings and prompt templates.
- Lazy-load heavy modules such as OCR and markdown/code highlighting.
- Virtualize conversation history lists.
- Use pooled `HttpClient` instances.
- Stream AI responses incrementally.
- Avoid WebView2 in MVP unless markdown requirements outgrow native rendering.
- Do not poll active selection continuously; react to input/focus events.
- Use source-generated JSON serialization for provider payloads in production.

## Windows installer and startup

Production packaging options:

- MSIX for clean install/update/uninstall and identity.
- Traditional installer if global hooks and startup integration need fewer MSIX constraints.

Startup:

- Register per-user startup entry only with explicit user consent.
- Provide tray menu to pause detection, open settings, and quit.

## Hardening checklist

- No plaintext secrets.
- No selected text in logs.
- Crash dumps disabled or scrubbed.
- Clipboard restoration tested for text, image, RTF, HTML, and file lists.
- App does not show overlay on password fields.
- Provider failover does not duplicate billing after first-token streaming failures without user awareness.
- All external requests have timeouts and cancellation.
- All background tasks stop cleanly on app shutdown.
