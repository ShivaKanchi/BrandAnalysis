import json
import time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Awaitable, AsyncGenerator

logger = logging.getLogger("BrandAnalysis.Workflow")


class BaseWorkflow:
    """
    Base DAG Workflow Orchestrator.
    Manages node state machines, React Flow graph format, execution telemetry,
    and Server-Sent Events (SSE) streaming for visual agent workflows.
    """

    def __init__(self, id: str, name: str, description: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.node_handlers: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}
        self.execution_order: List[str] = []

    def add_node(
        self,
        node_id: str,
        label: str,
        description: str = "",
        position: Optional[Dict[str, int]] = None,
        handler: Optional[Callable[..., Awaitable[Dict[str, Any]]]] = None,
    ):
        """Adds a node to the workflow graph conforming to React Flow node structure."""
        if position is None:
            idx = len(self.nodes)
            position = {"x": 100 + (idx * 260), "y": 200}

        node = {
            "id": node_id,
            "type": "workflowNode",
            "position": position,
            "data": {
                "id": node_id,
                "label": label,
                "description": description,
                "status": "idle",  # idle, running, completed, error, skipped
                "started_at": None,
                "completed_at": None,
                "duration_ms": 0.0,
                "logs": [],
                "output": {},
                "error": None,
            },
        }
        self.nodes.append(node)
        self.execution_order.append(node_id)
        if handler:
            self.node_handlers[node_id] = handler

    def add_edge(self, source: str, target: str, animated: bool = False):
        """Adds a directional edge between two nodes conforming to React Flow edge structure."""
        edge = {
            "id": f"e-{source}-{target}",
            "source": source,
            "target": target,
            "animated": animated,
        }
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        for n in self.nodes:
            if n["id"] == node_id:
                return n
        return None

    def get_graph(self) -> Dict[str, Any]:
        """Returns the full DAG graph structure for React Flow consumption."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [dict(n) for n in self.nodes],
            "edges": [dict(e) for e in self.edges],
        }

    def reset(self):
        """Resets all node states back to idle for a fresh execution run."""
        for node in self.nodes:
            node["data"]["status"] = "idle"
            node["data"]["started_at"] = None
            node["data"]["completed_at"] = None
            node["data"]["duration_ms"] = 0.0
            node["data"]["logs"] = []
            node["data"]["output"] = {}
            node["data"]["error"] = None
        for edge in self.edges:
            edge["animated"] = False

    def _set_edge_animation(self, target_node_id: str, animated: bool):
        for edge in self.edges:
            if edge["target"] == target_node_id:
                edge["animated"] = animated

    def _format_sse(self, event_data: Dict[str, Any]) -> str:
        """Formats a dictionary into an SSE compliant message string."""
        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

    async def stream_events(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Executes the workflow nodes in DAG sequence and streams real-time SSE events.
        Yields:
            data: {"event": "...", "node_id": "...", ...}\n\n
        """
        self.reset()
        workflow_start_time = time.time()
        start_timestamp = datetime.utcnow().isoformat()

        yield self._format_sse({
            "event": "workflow_start",
            "workflow_id": self.id,
            "workflow_name": self.name,
            "timestamp": start_timestamp,
            "context": {k: v for k, v in context.items() if not str(k).startswith("_") and not isinstance(v, (bytes, bytearray))},
        })

        event_queue: asyncio.Queue = asyncio.Queue()

        for node_id in self.execution_order:
            node = self.get_node(node_id)
            if not node:
                continue

            node_data = node["data"]

            # Check if previous steps flagged a workflow halt or branch skip
            if context.get(f"_skip_{node_id}") or context.get("_stop_workflow"):
                node_data["status"] = "skipped"
                yield self._format_sse({
                    "event": "node_skip",
                    "workflow_id": self.id,
                    "node_id": node_id,
                    "reason": context.get(f"_skip_reason_{node_id}", "Diverted by prior gate"),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                continue

            # Node starting
            start_ts = datetime.utcnow().isoformat()
            node_data["status"] = "running"
            node_data["started_at"] = start_ts
            self._set_edge_animation(node_id, True)

            yield self._format_sse({
                "event": "node_start",
                "workflow_id": self.id,
                "node_id": node_id,
                "label": node_data["label"],
                "timestamp": start_ts,
            })

            async def node_log(msg: str, level: str = "info"):
                log_entry = {
                    "time": datetime.utcnow().strftime("%H:%M:%S"),
                    "message": msg,
                    "level": level,
                }
                node_data["logs"].append(log_entry)
                await event_queue.put({
                    "event": "node_log",
                    "workflow_id": self.id,
                    "node_id": node_id,
                    "log": log_entry,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            handler = self.node_handlers.get(node_id)
            node_start_clock = time.time()
            output: Dict[str, Any] = {}
            error_occurred = False

            if handler:
                try:
                    # Run handler in a task so log events can be drained concurrently
                    handler_task = asyncio.create_task(handler(context, node_log))

                    while not handler_task.done():
                        # Drain any logs queued during execution
                        while not event_queue.empty():
                            evt = event_queue.get_nowait()
                            yield self._format_sse(evt)
                        await asyncio.sleep(0.05)

                    output = await handler_task

                    # Drain remaining logs
                    while not event_queue.empty():
                        evt = event_queue.get_nowait()
                        yield self._format_sse(evt)

                    # Update context with output
                    if isinstance(output, dict):
                        context.update(output)

                except Exception as e:
                    error_occurred = True
                    err_msg = str(e)
                    logger.exception(f"Error in node {node_id}: {err_msg}")
                    node_data["status"] = "error"
                    node_data["error"] = err_msg
                    node_duration = round((time.time() - node_start_clock) * 1000, 2)
                    node_data["duration_ms"] = node_duration
                    node_data["completed_at"] = datetime.utcnow().isoformat()
                    self._set_edge_animation(node_id, False)

                    # Drain any remaining logs
                    while not event_queue.empty():
                        evt = event_queue.get_nowait()
                        yield self._format_sse(evt)

                    yield self._format_sse({
                        "event": "node_error",
                        "workflow_id": self.id,
                        "node_id": node_id,
                        "error": err_msg,
                        "duration_ms": node_duration,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    break
            else:
                # No handler, marked as pass-through
                output = {"status": "passed"}

            if not error_occurred:
                node_duration = round((time.time() - node_start_clock) * 1000, 2)
                node_data["status"] = "completed"
                node_data["output"] = output or {}
                node_data["duration_ms"] = node_duration
                node_data["completed_at"] = datetime.utcnow().isoformat()
                self._set_edge_animation(node_id, False)

                yield self._format_sse({
                    "event": "node_complete",
                    "workflow_id": self.id,
                    "node_id": node_id,
                    "label": node_data["label"],
                    "output": output,
                    "duration_ms": node_duration,
                    "timestamp": datetime.utcnow().isoformat(),
                })

        total_duration = round((time.time() - workflow_start_time) * 1000, 2)
        final_status = "completed" if not any(n["data"]["status"] == "error" for n in self.nodes) else "error"

        yield self._format_sse({
            "event": "workflow_complete",
            "workflow_id": self.id,
            "status": final_status,
            "total_duration_ms": total_duration,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "nodes_total": len(self.nodes),
                "nodes_completed": sum(1 for n in self.nodes if n["data"]["status"] == "completed"),
                "nodes_skipped": sum(1 for n in self.nodes if n["data"]["status"] == "skipped"),
                "nodes_error": sum(1 for n in self.nodes if n["data"]["status"] == "error"),
            },
        })
