import os
from mcp.server.fastmcp import FastMCP
from redis import Redis
from pymongo import MongoClient
from pydantic import BaseModel, Field, ValidationError
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

# Define the server version. In a real application, this might be loaded
# from an environment variable or a configuration file at startup.
# For now, it's hardcoded as reading pyproject.toml was denied.
SERVER_VERSION = "1.0.0"

# --- Pydantic Schemas for validation based on .setup/poma_project_details.md ---

class AuditLogEntry(BaseModel):
    log_id: str = Field(..., description="Unique identifier for the audit log entry.")
    timestamp: datetime = Field(..., description="Timestamp of when the event occurred.")
    module: str = Field(..., description="The module or component that generated the audit event.")
    procedure: str = Field(..., description="The specific procedure or function executed.")
    inputs: Dict[str, Any] = Field(..., description="A dictionary of input parameters for the procedure.")
    outputs: Dict[str, Any] = Field(..., description="A dictionary of output results from the procedure.")
    status: str = Field(..., description="The status of the operation (e.g., 'success', 'failure', 'pending').")
    session_id: Optional[str] = Field(None, description="Optional: ID of the user session.")
    workflow_id: Optional[str] = Field(None, description="Optional: ID of the workflow associated with the event.")
    user_id: Optional[str] = Field(None, description="Optional: ID of the user who initiated the event.")
    rationale: Optional[str] = Field(None, description="Optional: Rationale or explanation for the event.")
    error_code: Optional[str] = Field(None, description="Optional: Error code if the status is 'failure'.")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CCWJPatch(BaseModel):
    patch_type: str = Field(..., description="Type of patch (e.g., 'add', 'remove', 'replace').")
    target_id: str = Field(..., description="The ID of the CCWJ element being patched.")
    changes: Dict[str, Any] = Field({}, description="A dictionary representing the changes to apply.")

    class Config:
        extra = 'allow'

class FeedbackEntry(BaseModel):
    feedback_type: str = Field(..., description="Type of feedback (e.g., 'bug_report', 'feature_request', 'general').")
    user_id: Optional[str] = Field(None, description="Optional: ID of the user providing feedback.")
    message: str = Field(..., description="The detailed feedback message.")
    rating: Optional[int] = Field(None, description="Optional: A numerical rating, if applicable.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the feedback was submitted.")

    class Config:
        extra = 'allow'
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class WorkflowEvent(BaseModel):
    event_name: str = Field(..., description="The name of the workflow event (e.g., 'workflow_started', 'step_completed').")
    workflow_id: str = Field(..., description="The ID of the workflow associated with this event.")
    status: str = Field(..., description="The status of the workflow or step (e.g., 'running', 'completed', 'failed').")
    payload: Dict[str, Any] = Field({}, description="Optional: Additional data related to the event.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the event occurred.")

    class Config:
        extra = 'allow'
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProcedureDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    inputs: Optional[List[str]] = None
    outputs: Optional[List[str]] = None
    micro_prompts: Optional[List[str]] = None
    definition_schema: Optional[Dict[str, Any]] = None
    ruleset: Optional[Dict[str, Any]] = None

class ModuleRegistryEntry(BaseModel):
    module_name: str = Field(..., description="The unique name of the module.")
    emoji: Optional[str] = Field(None, description="Optional: An emoji representing the module.")
    version: str = Field(..., description="The version of the module.")
    status: str = Field(..., description="The current status of the module (e.g., 'active', 'deprecated', 'beta').")
    scope: Optional[str] = Field(None, description="Optional: The scope or domain of the module.")
    description: Optional[str] = Field(None, description="Optional: A brief description of what the module does.")
    outputs: Optional[str] = Field(None, description="Optional: Description of the module's typical outputs.")
    dependencies: Optional[List[str]] = Field(None, description="Optional: A list of other modules or services this module depends on.")
    owner: Optional[str] = Field(None, description="Optional: The owner or maintainer of the module.")
    invocation_examples: Optional[List[str]] = Field(None, description="Optional: Examples of how to invoke the module.")
    procedures: Optional[List[ProcedureDefinition]] = Field(
        None, description="Optional: List of procedures or callable actions in the module."
    )
    created_at: Optional[str] = Field(None, description="Optional: Creation timestamp (ISO8601).")
    updated_at: Optional[str] = Field(None, description="Optional: Last updated timestamp (ISO8601).")
    
    class Config:
        extra = 'allow'

class WorkflowPhase(BaseModel):
    phase_id: str = Field(..., description="Unique identifier for the phase/step.")
    name: str = Field(..., description="Phase/step name.")
    status: Optional[str] = Field(None, description="Status of this phase ('pending', 'in_progress', 'completed', etc.).")
    modules_invoked: Optional[List[str]] = Field(None, description="Modules/procedures used in this phase.")
    inputs: Optional[Dict[str, Any]] = Field(None, description="Input data for the phase.")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Outputs/results produced by the phase.")
    audit_log_ids: Optional[List[str]] = Field(None, description="References to audit log entries for this phase.")
    start_time: Optional[str] = Field(None, description="ISO8601 start timestamp.")
    end_time: Optional[str] = Field(None, description="ISO8601 end timestamp.")

class Workflow(BaseModel):
    workflow_id: str = Field(..., description="Unique identifier for the workflow.")
    name: str = Field(..., description="The name of the workflow.")
    phases: List[WorkflowPhase] = Field(..., description="List of workflow phases/steps, in order.")
    status: Optional[str] = Field(None, description="Workflow status (e.g., 'created', 'running', 'completed', 'failed').")
    current_phase_id: Optional[str] = Field(None, description="ID of the currently active phase.")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO8601).")
    updated_at: Optional[str] = Field(None, description="Last updated timestamp (ISO8601).")

    class Config:
        extra = 'allow'

class ChatMessage(BaseModel):
    message_id: str = Field(..., description="Unique identifier for the chat message.")
    session_id: str = Field(..., description="The ID of the chat session.")
    timestamp: datetime = Field(..., description="Timestamp of when the message was sent.")
    sender: str = Field(..., description="The sender of the message (e.g., 'user', 'system', 'LLM', 'agent').")
    content: str = Field(..., description="The content of the chat message.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional: Additional metadata associated with the message.")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CCWJSnapshot(BaseModel):
    snapshot_id: str = Field(..., description="Unique identifier for the CCWJ snapshot.")
    timestamp: datetime = Field(..., description="Timestamp of when the snapshot was created.")
    data: Dict[str, Any] = Field({}, description="The full CCWJ data at the time of the snapshot.")

    class Config:
        extra = 'allow'
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalyticsReport(BaseModel):
    report_name: str = Field(..., description="The name of the analytics report.")
    timestamp: datetime = Field(..., description="Timestamp of when the report was generated.")
    metrics: Dict[str, Any] = Field({}, description="A dictionary of metrics included in the report.")

    class Config:
        extra = 'allow'
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Load database URIs from environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/poma")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize database connections
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.poma
    # You can add a test connection here if needed, e.g., db.command('ping')
except Exception as e:
    # In a real application, you might log this error or handle it more gracefully
    raise ConnectionError(f"Could not connect to MongoDB: {e}") from e

try:
    redis_client = Redis.from_url(REDIS_URL)
    # Test connection
    redis_client.ping()
except Exception as e:
    raise ConnectionError(f"Could not connect to Redis: {e}") from e

# Ensure unique index for module_registry collection
try:
    db.module_registry.create_index(
        {"module_name": 1, "version": 1},
        unique=True
    )
    print("MongoDB unique index on module_registry (module_name, version) ensured.")
except Exception as e:
    print(f"Error ensuring unique index for module_registry: {e}")

# Create an MCP server instance
mcp = FastMCP("POMA-mcp Server")

@mcp.tool()
def get_server_version() -> str:
    """Returns the current version of the POMA-mcp server."""
    return SERVER_VERSION

@mcp.tool()
def get_db_status() -> dict:
    """Returns the connection status of MongoDB and Redis."""
    mongo_status = False
    redis_status = False
    try:
        mongo_client.admin.command('ping')
        mongo_status = True
    except Exception:
        pass
    try:
        redis_client.ping()
        redis_status = True
    except Exception:
        pass
    return {"mongodb_connected": mongo_status, "redis_connected": redis_status}

@mcp.tool()
def get_current_timestamp() -> str:
    """Returns the current day and time (now) for this system's timezone."""
    return datetime.now().isoformat()

@mcp.tool()
def log_audit_event(audit_entry: AuditLogEntry) -> str:
    """
    Logs an audit event to the Redis stream 'mcp:audit_log_stream' and MongoDB 'audit_logs' collection.

    Args:
        audit_entry: The log record to be stored, following the AuditLogEntry schema.
    """
    try:
        # The input 'audit_entry' is already validated by Pydantic as part of FastMCP's argument parsing
        # Log to Redis stream
        redis_client.xadd("mcp:audit_log_stream", {"data": json.dumps(audit_entry.model_dump(by_alias=True))})
        # Log to MongoDB
        db.audit_logs.insert_one(audit_entry.model_dump(by_alias=True))
        return "Audit event logged successfully to Redis and MongoDB."
    except Exception as e:
        raise e

@mcp.tool()
def publish_ccwj_update(ccwj_patch: CCWJPatch) -> str:
    """
    Publishes a Current Context Window JSON (CCWJ) update to the Redis stream 'mcp:ccwj_update_stream'.
    The ccwj_patch should conform to the CCWJ Delta/Update schema.
    """
    try:
        # The input 'ccwj_patch' is already validated by Pydantic
        redis_client.xadd("mcp:ccwj_update_stream", {"data": json.dumps(ccwj_patch.model_dump(by_alias=True))})
        return "CCWJ update published successfully."
    except Exception as e:
        raise e

@mcp.tool()
def publish_user_feedback(feedback_entry: FeedbackEntry) -> str:
    """
    Publishes user feedback to the Redis stream 'mcp:user_feedback' and archives it in MongoDB 'user_feedback' collection.
    The feedback_entry should conform to the FeedbackEntry schema.
    """
    try:
        # The input 'feedback_entry' is already validated by Pydantic
        # Publish to Redis stream
        redis_client.xadd("mcp:user_feedback", {"data": json.dumps(feedback_entry.model_dump(by_alias=True))})
        # Archive to MongoDB
        db.user_feedback.insert_one(feedback_entry.model_dump(by_alias=True))
        return "User feedback published to Redis and archived in MongoDB successfully."
    except Exception as e:
        raise e

@mcp.tool()
def publish_workflow_event(workflow_event: WorkflowEvent) -> str:
    """
    Publishes a workflow event to the Redis stream 'mcp:workflow_events'.
    The workflow_event should conform to the WorkflowEvent schema.
    """
    try:
        # The input 'workflow_event' is already validated by Pydantic
        redis_client.xadd("mcp:workflow_events", {"data": json.dumps(workflow_event.model_dump(by_alias=True))})
        return "Workflow event published successfully."
    except Exception as e:
        raise e

@mcp.tool()
def acquire_lock(resource_name: str, timeout_seconds: int = 30) -> bool:
    """
    Acquires a distributed lock for a given resource.
    Returns True if the lock was acquired, False otherwise.
    """
    try:
        # Set if not exists, expires after N seconds
        return bool(redis_client.set(f"mcp:locks:{resource_name}", "locked", ex=timeout_seconds, nx=True))
    except Exception as e:
        raise e

@mcp.tool()
def release_lock(resource_name: str) -> bool:
    """
    Releases a distributed lock for a given resource.
    Returns True if the lock was released, False otherwise.
    """
    try:
        return redis_client.delete(f"mcp:locks:{resource_name}") == 1
    except Exception as e:
        raise e

@mcp.tool()
def increment_rate_limit(key: str, window_seconds: int = 60) -> int:
    """
    Increments the rate limit counter for a given key and sets its expiry.
    Returns the current count.
    """
    try:
        pipe = redis_client.pipeline()
        pipe.incr(f"mcp:rate:{key}")
        pipe.expire(f"mcp:rate:{key}", window_seconds)
        count, _ = pipe.execute()
        return count
    except Exception as e:
        raise e

@mcp.tool()
def get_rate_limit(key: str) -> int:
    """
    Gets the current rate limit count for a given key.
    Returns the count, or -1 if the key does not exist or on error.
    """
    try:
        count_bytes = redis_client.get(f"mcp:rate:{key}")
        return int(count_bytes.decode('utf-8')) if isinstance(count_bytes, bytes) else 0
    except Exception as e:
        raise e

@mcp.tool()
def add_module_registry_entry(module_entry: ModuleRegistryEntry) -> str:
    """Adds a module registry entry to MongoDB."""
    try:
        now = datetime.utcnow().isoformat()
        module_entry.created_at = now
        module_entry.updated_at = now
        db.module_registry.insert_one(module_entry.model_dump(by_alias=True))
        return "Module registry entry added successfully."
    except Exception as e:
        raise e

@mcp.tool()
def update_module_registry_entry(module_name: str, update: dict) -> str:
    """Updates a module registry entry in MongoDB."""
    try:
        now = datetime.utcnow().isoformat()
        update["updated_at"] = now
        result = db.module_registry.update_one({"module_name": module_name}, {"$set": update})
        if result.matched_count:
            return "Module registry entry updated successfully."
        else:
            return "Module registry entry not found."
    except Exception as e:
        raise e

@mcp.tool()
def get_module_registry_entry(module_name: str) -> dict:
    """Fetches a module registry entry from MongoDB."""
    try:
        result = db.module_registry.find_one({"module_name": module_name})
        return result if result is not None else {}
    except Exception as e:
        raise e

@mcp.tool()
def create_workflow(workflow_doc: Workflow) -> str:
    """Creates a new workflow entry in MongoDB."""
    try:
        now = datetime.utcnow().isoformat()
        workflow_doc.created_at = now
        workflow_doc.updated_at = now
        db.workflows.insert_one(workflow_doc.model_dump(by_alias=True))
        return "Workflow created successfully."
    except Exception as e:
        raise e

@mcp.tool()
def get_workflow(workflow_id: str) -> dict:
    """Fetches a workflow entry from MongoDB."""
    try:
        result = db.workflows.find_one({"workflow_id": workflow_id})
        return result if result is not None else {}
    except Exception as e:
        raise e

@mcp.tool()
def update_workflow(workflow_id: str, update: dict) -> str:
    """Updates a workflow entry in MongoDB."""
    try:
        now = datetime.utcnow().isoformat()
        update["updated_at"] = now
        result = db.workflows.update_one({"workflow_id": workflow_id}, {"$set": update})
        if result.matched_count:
            return "Workflow updated successfully."
        else:
            return "Workflow not found."
    except Exception as e:
        raise e

@mcp.tool()
def log_chat_message(message_doc: ChatMessage) -> str:
    """Logs a chat message to MongoDB."""
    try:
        # The input 'message_doc' is already validated by Pydantic
        db.chat_history.insert_one({"data": json.dumps(message_doc.model_dump(by_alias=True))})
        return "Chat message logged successfully."
    except Exception as e:
        raise e

@mcp.tool()
def save_ccwj_snapshot(ccwj_obj: CCWJSnapshot) -> str:
    """Saves a CCWJ snapshot to MongoDB."""
    try:
        # The input 'ccwj_obj' is already validated by Pydantic
        db.ccwj_snapshots.insert_one({"data": json.dumps(ccwj_obj.model_dump(by_alias=True))})
        return "CCWJ snapshot saved successfully."
    except Exception as e:
        raise e

@mcp.tool()
def log_analytics_report(report_obj: AnalyticsReport) -> str:
    """Logs an analytics report to MongoDB."""
    try:
        # The input 'report_obj' is already validated by Pydantic
        db.analytics.insert_one({"data": json.dumps(report_obj.model_dump(by_alias=True))})
        return "Analytics report logged successfully."
    except Exception as e:
        raise e

if __name__ == "__main__":
    # Run the FastMCP server. By default, it will use stdio transport.
    mcp.run()
