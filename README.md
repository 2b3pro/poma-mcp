# POMA-mcp

A Python-based MCP server.

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/2b3pro/POMA-mcp.git
    cd POMA-mcp
    ```

2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the server, run:

```bash
python server.py
```

This will start the MCP server, which will be available for clients to connect to.

## Tools

This server provides the following tools:

### Redis/MongoDB Interaction Tools

- `get_server_version`: Returns the current version of the POMA-mcp server.
- `get_db_status`: Returns the connection status of MongoDB and Redis.
- `log_audit_event`: Logs an audit event to the Redis stream `mcp:audit_log_stream` and the MongoDB `audit_logs` collection.
- `publish_ccwj_update`: Publishes a Current Context Window JSON (CCWJ) update to the Redis stream `mcp:ccwj_update_stream`.
- `publish_user_feedback`: Publishes user feedback to the Redis stream `mcp:user_feedback` and archives it in the MongoDB `user_feedback` collection.
- `publish_workflow_event`: Publishes a workflow event to the Redis stream `mcp:workflow_events`.

### Redis-Specific Tools (Distributed Primitives)

- `acquire_lock`: Acquires a distributed lock for a given resource using Redis.
- `release_lock`: Releases a distributed lock for a given resource using Redis.
- `increment_rate_limit`: Increments a rate limit counter for a given key using Redis.
- `get_rate_limit`: Gets the current rate limit count for a given key using Redis.

### MongoDB-Specific Tools (Data Management)

- `add_module_registry_entry`: Adds a module registry entry to the MongoDB `module_registry` collection.
- `update_module_registry_entry`: Updates an existing module registry entry in the MongoDB `module_registry` collection.
- `get_module_registry_entry`: Fetches a module registry entry from the MongoDB `module_registry` collection.
- `create_workflow`: Creates a new workflow entry in the MongoDB `workflows` collection.
- `get_workflow`: Fetches a workflow entry from the MongoDB `workflows` collection.
- `update_workflow`: Updates an existing workflow entry in the MongoDB `workflows` collection.
- `log_chat_message`: Logs a chat message to the MongoDB `chat_history` collection.
- `save_ccwj_snapshot`: Saves a Current Context Window JSON (CCWJ) snapshot to the MongoDB `ccwj_snapshots` collection.
- `log_analytics_report`: Logs an analytics report to the MongoDB `analytics` collection.
