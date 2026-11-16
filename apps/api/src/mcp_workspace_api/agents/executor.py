from __future__ import annotations

import time
from typing import Any

from sqlalchemy import select

from mcp_workspace_api.agents.context_manager import resolve
from mcp_workspace_api.agents.evidence_cache import merge_read_evidence
from mcp_workspace_api.agents.mock.artifact_content import artifact_content
from mcp_workspace_api.agents.mock.planner import fake_plan
from mcp_workspace_api.agents.model_evidence import evidence_json
from mcp_workspace_api.agents.model_history import conversation_history
from mcp_workspace_api.agents.summarizer import summarize
from mcp_workspace_api.core.execution_context import Runtime, approval_json, artifact_json
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import Artifact, Conversation, Message, Run, User, now
from mcp_workspace_api.llm.providers.openai_compatible import cloud_step


async def execute_run(
    runtime: Runtime, run_id: str, approved: dict[str, str] | None, *, deadline: float | None = None
) -> None:
    with runtime.db.session() as session:
        run = session.get(Run, run_id)
        if not run or run.status in {"completed", "cancelled", "failed"}:
            return
        run.status = "running"
        user_id, prompt, state = run.user_id, run.prompt, run.state
        conversation_id = run.conversation_id
        prior = session.scalar(
            select(Run)
            .where(
                Run.user_id == user_id,
                Run.conversation_id == run.conversation_id,
                Run.id != run_id,
                Run.status == "completed",
            )
            .order_by(Run.created_at.desc())
            .limit(1)
        )
        previous = state.get("previous_context") or (prior.state if prior else {})
    previous = {
        "results": previous.get("evidence_results", previous.get("results", [])),
        "references": previous.get("references", {}),
    }
    if runtime.settings.mode == "live" and runtime.settings.llm_provider == "fake":
        raise Denied(
            "PROVIDER_UNAVAILABLE",
            "FakeLLM is for synthetic demo data; configure a real model for live chat",
        )
    history = conversation_history(runtime, user_id, conversation_id, prompt)
    model_messages = list(state.get("model_messages", []))
    catalog = await runtime.catalog(user_id)
    results = list(state.get("results", []))
    steps = list(
        state.get("steps")
        or (fake_plan(prompt, previous) if runtime.settings.llm_provider == "fake" else [])
    )
    position = int(state.get("position", 0))

    def checkpoint(phase: str) -> None:
        nonlocal state
        state = {
            **state,
            "steps": steps,
            "position": position,
            "results": results,
            "model_messages": model_messages,
            "phase": phase,
            "previous_context": previous,
        }
        with runtime.db.session() as session:
            current = session.get(Run, run_id)
            if current:
                current.state = state

    runtime.emit(
        run_id,
        "run.started",
        {
            "provider": runtime.settings.llm_provider,
            "model": runtime.settings.llm_model or "FakeLLM",
            "synthetic": runtime.settings.mode == "mock",
        },
    )
    final = ""
    final_streamed = False
    for _ in range(runtime.settings.max_tool_calls):
        if len(results) >= runtime.settings.max_tool_calls:
            raise Denied("LIMIT_EXCEEDED", "Workflow reached its total tool-call limit")
        with runtime.db.session() as session:
            current = session.get(Run, run_id)
            if not current or current.status == "cancelled":
                return
        if runtime.settings.llm_provider == "openai_compatible":
            checkpoint("model")
            step = state.get("pending_step") if approved else None
            step = step or await cloud_step(
                runtime,
                user_id,
                prompt,
                results,
                catalog,
                previous.get("results", []),
                history=history,
                turn_messages=model_messages,
                on_delta=lambda text: runtime.emit(run_id, "message.delta", {"text": text}),
                remaining_seconds=max(0.001, deadline - time.monotonic()) if deadline else None,
                run_id=run_id,
            )
            if step.get("usage"):
                runtime.emit(
                    run_id,
                    "model.usage",
                    {"model": runtime.settings.llm_model, "usage": step["usage"]},
                )
            if step.get("content"):
                final = step["content"]
                final_streamed = step.get("streamed", False)
                break
            if step.get("assistant_message") and not approved:
                model_messages.append(step["assistant_message"])
        else:
            if position >= len(steps):
                break
            step = steps[position]
        name = step["tool"]
        if name not in runtime.tools:
            raise Denied("PERMISSION_DENIED", "The model selected an unknown tool")
        args = resolve(step["arguments"], results, previous)
        if name.startswith("artifact.create_") and runtime.settings.llm_provider == "fake":
            args = artifact_content(args, results or previous.get("results", []))
        definition = runtime.tools[name]
        runtime.policy.authorize(user_id, definition)
        if runtime.policy.needs_approval(definition) and not approved:
            approval = await runtime.propose(user_id, run_id, name, args)
            with runtime.db.session() as session:
                current = session.get(Run, run_id)
                if current and current.status != "cancelled":
                    current.status = "needs_approval"
                    current.state = {
                        **state,
                        "steps": steps,
                        "position": position,
                        "results": results,
                        "pending_step": {"tool": name, "arguments": args},
                        "model_messages": model_messages,
                    }
                    if step.get("call_id"):
                        current.state["pending_step"]["call_id"] = step["call_id"]
            runtime.emit(run_id, "approval.required", approval_json(approval))
            return
        runtime.emit(
            run_id,
            "tool.started",
            {
                "tool": name,
                "server": definition.server,
                "arguments": {"summary": "Validated arguments", "schema_digest": definition.digest},
            },
        )
        checkpoint("tool")
        result = await runtime.invoke(user_id, name, args, run_id, approved)
        approved = None
        if result.status != "success":
            raise Denied(result.code or "TOOL_FAILED", "; ".join(result.warnings))
        results.append({"tool": name, **result.model_dump(mode="json")})
        if step.get("call_id"):
            model_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": step["call_id"],
                    "content": evidence_json([result.model_dump(mode="json")], 60000)[1:-1],
                }
            )
        if name.startswith("artifact.create_"):
            citations = [
                source
                for item in (
                    results
                    if any(item.get("sources") for item in results)
                    else previous.get("results", [])
                )
                for source in item.get("sources", [])
            ]
            citations = list(
                {
                    (source["provider"], source["resource_id"]): source for source in citations
                }.values()
            )
            results[-1]["sources"] = citations
            with runtime.db.session() as session:
                artifact = session.get(Artifact, result.data["id"])
                if artifact:
                    artifact.sources = citations
        position += 1
        checkpoint("model")
    else:
        raise Denied("LIMIT_EXCEEDED", "Workflow reached its configured tool-call limit")
    cached_evidence = merge_read_evidence(runtime.tools, previous.get("results", []), results)
    sources = list(
        {
            (source["provider"], source["resource_id"]): source
            for item in [*cached_evidence, *results]
            for source in item.get("sources", [])
        }.values()
    )
    if any(item["tool"] == "demo.ping" for item in results) and "tool" in prompt.lower():
        final = "Currently authorized tools discovered over MCP:\n\n" + "\n".join(
            row["name"] for row in catalog if row["enabled"]
        )
    with runtime.db.session() as session:
        artifacts = [
            artifact_json(row)
            for row in session.scalars(
                select(Artifact).where(Artifact.run_id == run_id, Artifact.user_id == user_id)
            )
        ]
        run = session.get(Run, run_id)
        user = session.get(User, user_id)
        if not run or not user or user.deleted or run.status == "cancelled":
            return
        if not final:
            final = summarize(results)
            if not results:
                final = "I cannot act on instructions that request credentials or bypass approvals."
            final = "Synthetic demo result - based on the retrieved records.\n\n" + final
            if artifacts:
                final += f"\n\nCreated {len(artifacts)} validated files."
            writes = [
                item
                for item in results
                if runtime.policy.needs_approval(runtime.tools[item["tool"]])
            ]
            if writes:
                final += "\n\nApproved action completed: " + ", ".join(
                    item["tool"] for item in writes
                )
        workspace_files = runtime.workspace_file_service.for_run(user_id, run_id)
        session.add(
            Message(
                user_id=user_id,
                conversation_id=run.conversation_id,
                role="assistant",
                content=final,
                sources=sources,
                artifacts=artifacts,
                workspace_files=workspace_files,
            )
        )
        conversation = session.get(Conversation, run.conversation_id)
        if conversation:
            conversation.updated_at = now()
        refs: dict[str, Any] = dict(previous.get("references", {}))
        for item in results:
            data = item["data"]
            if data.get("draft_id"):
                refs["draft"] = data["draft_id"]
            for key, target in (("messages", "message"), ("events", "event"), ("files", "file")):
                if data.get(key):
                    row = data[key][0]
                    refs[target] = row.get(target + "_id") or row.get("id")
                    if row.get("thread_id"):
                        refs["thread"] = row["thread_id"]
                    if key == "events" and row.get("start", {}).get("dateTime"):
                        refs["event_start"] = row["start"]["dateTime"]
                        refs["event_end"] = row["end"]["dateTime"]
        run.status, run.state = (
            "completed",
            {**state, "references": refs, "evidence_results": cached_evidence},
        )
    if not final_streamed:
        for offset in range(0, len(final), 160):
            runtime.emit(run_id, "message.delta", {"text": final[offset : offset + 160]})
    runtime.emit(
        run_id,
        "run.completed",
        {
            "content": final,
            "sources": sources,
            "artifacts": artifacts,
            "workspace_files": workspace_files,
        },
    )
