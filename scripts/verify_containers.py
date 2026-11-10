"""Verify the local mock container or Compose stack and remove only test resources."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def run(command: list[str]) -> str:
    return subprocess.run(
        command, capture_output=True, text=True, check=True, timeout=300
    ).stdout.strip()


def frontend(command: list[str]) -> None:
    run(
        command
        + [
            "python",
            "-c",
            "import urllib.request; "
            "assert b'<div id=\"root\">' in "
            "urllib.request.urlopen('http://127.0.0.1:8000/').read(); "
            "from mcp_workspace_evaluations.case_loader import cases; "
            "assert len(cases()) == 52",
        ]
    )


def container_proof(image: str) -> dict[str, Any]:
    container = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            "workspace-check-" + uuid.uuid4().hex[:10],
            "--network",
            "none",
            "--memory",
            "8g",
            "--cpus",
            "2",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--tmpfs",
            "/app/.local:uid=10001,gid=10001,mode=0700,size=256m",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=64m",
            image,
        ]
    )
    proof: dict[str, Any] = {}
    try:
        execute = ["docker", "exec", container]
        for _ in range(60):
            try:
                run(
                    execute
                    + [
                        "python",
                        "-c",
                        "import urllib.request; "
                        "urllib.request.urlopen('http://127.0.0.1:8000/api/ready',timeout=2)",
                    ]
                )
                break
            except subprocess.CalledProcessError:
                time.sleep(0.25)
        else:
            raise RuntimeError("Container readiness failed")
        proof["smoke"] = json.loads(run(execute + ["workspace-ai", "smoke"]))
        frontend(execute)
        config = json.loads(run(["docker", "inspect", container]))[0]
        proof.update(
            image=config["Image"],
            container_user=config["Config"]["User"],
            network_mode=config["HostConfig"]["NetworkMode"],
            memory_limit_bytes=config["HostConfig"]["Memory"],
            read_only_rootfs=config["HostConfig"]["ReadonlyRootfs"],
            frontend_html="PASS",
            packaged_evaluation_cases=52,
            cgroup_memory_bytes=json.loads(
                run(
                    execute
                    + [
                        "python",
                        "-c",
                        "from pathlib import Path; import json; print(json.dumps({n: "
                        "int(Path('/sys/fs/cgroup',n).read_text()) "
                        "for n in ['memory.current','memory.peak']}))",
                    ]
                )
            ),
            note="Synthetic no-network run under an 8 GiB limit; not a physical-machine benchmark.",
        )
    finally:
        run(["docker", "rm", "-f", container])
    return {**proof, "cleanup": "PASS"}


def compose_proof() -> dict[str, Any]:
    project = "workspace-check-" + uuid.uuid4().hex[:10]
    with tempfile.TemporaryDirectory(prefix="workspace-compose-config-") as temporary:
        # Select the installed plugins without changing an operator's Docker configuration.
        Path(temporary, "config.json").write_text(
            json.dumps({"cliPluginsExtraDirs": ["/usr/libexec/docker/cli-plugins"]})
        )
        command = ["docker", "--config", temporary, "compose", "-p", project]
        try:
            run(command + ["up", "--build", "--wait"])
            execute = command + ["exec", "-T", "workspace"]
            smoke = json.loads(run(execute + ["workspace-ai", "smoke"]))
            frontend(execute)
            services = json.loads(run(command + ["ps", "--format", "json"]))
        finally:
            run(command + ["down", "--volumes", "--remove-orphans"])
    return {
        "startup": "PASS",
        "project": project,
        "smoke": smoke,
        "services": services,
        "frontend_html": "PASS",
        "packaged_evaluation_cases": 52,
        "cleanup": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose", action="store_true")
    parser.add_argument("--image", default="mcp-workspace-ai:reorganized")
    args = parser.parse_args()
    proof = compose_proof() if args.compose else container_proof(args.image)
    proof.update(status="PASS", measured_at=datetime.now(UTC).isoformat())
    output = Path("demo/evidence/reorganization") / (
        "compose-proof.json" if args.compose else "container-proof.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
