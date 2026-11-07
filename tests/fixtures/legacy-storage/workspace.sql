BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO "alembic_version" VALUES('0002');
CREATE TABLE approvals (
	run_id VARCHAR(64) NOT NULL, 
	tool VARCHAR NOT NULL, 
	arguments JSON NOT NULL, 
	snapshot JSON NOT NULL, 
	action_digest VARCHAR NOT NULL, 
	account_id VARCHAR NOT NULL, 
	expires_at DOUBLE NOT NULL, 
	status VARCHAR NOT NULL, 
	capability_hash VARCHAR NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES runs (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO "approvals" VALUES('legacy-running','gmail.create_draft','{"to": ["alex@example.invalid"], "subject": "Legacy synthetic draft", "body_text": "Retained exact body"}','{}','synthetic-digest','legacy-account',4102444800.0,'consumed','','legacy-consumed','legacy-owner',4102444800.0);
INSERT INTO "approvals" VALUES('legacy-pending','gmail.create_draft','{"to": ["alex@example.invalid"], "subject": "Legacy synthetic draft", "body_text": "Retained exact body"}','{}','synthetic-digest','legacy-account',4102444800.0,'pending','','legacy-approval','legacy-owner',4102444800.0);
CREATE TABLE artifacts (
	run_id VARCHAR(64), 
	title VARCHAR NOT NULL, 
	format VARCHAR NOT NULL, 
	mime_type VARCHAR NOT NULL, 
	storage_key VARCHAR NOT NULL, 
	size INTEGER NOT NULL, 
	sha256 VARCHAR NOT NULL, 
	validated BOOLEAN NOT NULL, 
	sources JSON NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES runs (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO "artifacts" VALUES('legacy-running','Legacy synthetic report','csv','text/csv','artifacts/legacy-owner/legacy.csv',34,'403772913a16efedd78a993ac536f8d8f4342d8b2f994f4746e518d848dc695d',1,'[]','legacy-artifact','legacy-owner',4102444800.0);
CREATE TABLE conversations (
	title VARCHAR NOT NULL, 
	updated_at DOUBLE NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO "conversations" VALUES('Existing synthetic conversation',4102444800.0,'legacy-conversation','legacy-owner',4102444800.0);
CREATE TABLE google_accounts (
	subject VARCHAR NOT NULL, 
	credentials VARCHAR NOT NULL, 
	scopes JSON NOT NULL, 
	enabled JSON NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, key_version VARCHAR(64) DEFAULT 'v1' NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO "google_accounts" VALUES('synthetic-legacy-subject','gAAAAABq7rZWnXD0DAKOWF1StzP-jcW3zDI9x7dw3-Bu1eX6MOZfUrXu5MsSI3S85oqivbCT5uIfGPtx5VYXJmRsJ2fcKSkt0beaCOG5wmXQgZndzbjHhTA8EhCmWJndLO0PJDzRYh3BXIFIFzPTao5gSP6Q1IvzBZkQW9Fgi7cLFeBbtFNFqDvC-GoPMCju7cFLDgewv43s','["drive.file"]','["gmail", "calendar", "drive"]','legacy-account','legacy-owner',4102444800.0,'legacy-v1');
CREATE TABLE messages (
	conversation_id VARCHAR(64) NOT NULL, 
	role VARCHAR NOT NULL, 
	content VARCHAR NOT NULL, 
	sources JSON NOT NULL, 
	artifacts JSON NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO "messages" VALUES('legacy-conversation','assistant','Retained synthetic answer','[]','[]','legacy-message','legacy-owner',4102444800.0);
CREATE TABLE oauth_states (
	id VARCHAR(128) NOT NULL, 
	browser_hash VARCHAR NOT NULL, 
	user_id VARCHAR(64), 
	nonce VARCHAR NOT NULL, 
	verifier VARCHAR NOT NULL, 
	connector VARCHAR NOT NULL, 
	expires_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE operations (
	approval_id VARCHAR(64) NOT NULL, 
	status VARCHAR NOT NULL, 
	result JSON NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(approval_id) REFERENCES approvals (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (approval_id)
);
INSERT INTO "operations" VALUES('legacy-consumed','dispatched','{}','legacy-operation','legacy-owner',4102444800.0);
CREATE TABLE run_events (
	sequence INTEGER NOT NULL, 
	run_id VARCHAR(64) NOT NULL, 
	type VARCHAR NOT NULL, 
	data JSON NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES runs (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO "run_events" VALUES(1,'legacy-running','tool.started','{"tool": "gmail.create_draft", "server": "gmail"}','legacy-event','legacy-owner',4102444800.0);
CREATE TABLE runs (
	conversation_id VARCHAR(64) NOT NULL, 
	request_id VARCHAR(200) NOT NULL, 
	prompt VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	state JSON NOT NULL, 
	error VARCHAR NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (request_id)
);
INSERT INTO "runs" VALUES('legacy-conversation','legacy-running','Synthetic retained run','running','{"position": 1, "results": []}','','legacy-running','legacy-owner',4102444800.0);
INSERT INTO "runs" VALUES('legacy-conversation','legacy-pending','Synthetic retained run','needs_approval','{"position": 1, "results": []}','','legacy-pending','legacy-owner',4102444800.0);
CREATE TABLE sessions (
	token_hash VARCHAR(64) NOT NULL, 
	csrf VARCHAR NOT NULL, 
	expires_at DOUBLE NOT NULL, 
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	created_at DOUBLE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token_hash)
);
INSERT INTO "sessions" VALUES('7a881f912901576be201c21762d966c091335d4fff6ce1fc0a2dee3da4ab217a','synthetic-legacy-csrf',4102444800.0,'legacy-session','legacy-owner',4102444800.0);
CREATE TABLE users (
	id VARCHAR(64) NOT NULL, 
	subject VARCHAR(256) NOT NULL, 
	display_name VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	timezone VARCHAR NOT NULL, 
	llm_consent BOOLEAN NOT NULL, 
	consent_provider VARCHAR NOT NULL, 
	deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (subject)
);
INSERT INTO "users" VALUES('legacy-owner','synthetic-legacy-subject','Synthetic legacy owner','legacy@example.invalid','America/Chicago',0,'',0);
CREATE INDEX ix_conversations_user_id ON conversations (user_id);
CREATE INDEX ix_google_accounts_user_id ON google_accounts (user_id);
CREATE INDEX ix_sessions_user_id ON sessions (user_id);
CREATE INDEX ix_messages_conversation_id ON messages (conversation_id);
CREATE INDEX ix_messages_user_id ON messages (user_id);
CREATE INDEX ix_runs_conversation_id ON runs (conversation_id);
CREATE INDEX ix_runs_status ON runs (status);
CREATE INDEX ix_runs_user_id ON runs (user_id);
CREATE INDEX ix_approvals_run_id ON approvals (run_id);
CREATE INDEX ix_approvals_user_id ON approvals (user_id);
CREATE INDEX ix_artifacts_user_id ON artifacts (user_id);
CREATE INDEX ix_run_events_run_id ON run_events (run_id);
CREATE INDEX ix_run_events_sequence ON run_events (sequence);
CREATE INDEX ix_run_events_user_id ON run_events (user_id);
CREATE INDEX ix_operations_user_id ON operations (user_id);
COMMIT;
