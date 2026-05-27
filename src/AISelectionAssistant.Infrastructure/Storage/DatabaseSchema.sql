CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  selected_text_hash TEXT NOT NULL,
  selected_text_preview TEXT NOT NULL,
  source_process TEXT,
  source_window_title TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  is_pinned INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_conversations_text_hash ON conversations(selected_text_hash);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at_utc);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  provider_id TEXT,
  model_id TEXT,
  created_at_utc TEXT NOT NULL,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS prompt_actions (
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
