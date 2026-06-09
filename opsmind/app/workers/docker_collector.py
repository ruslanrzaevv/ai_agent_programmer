from __future__ import annotations
import asyncio
import re
import ssl
import tempfile
import os
from datetime import datetime, timezone
import json

import docker
import docker.errors
from tenacity import retry, stop_never, wait_exponential, retry_if_exception_type
from app.core.logging import get_logger
from app.db.redis import cache
from app.models.models import LogEntry, LogLevel, LogSource, Project
from app.db.redis import get_redis

logger = get_logger("docker_collector")


LEVEL_PATTERNS = {
    LogLevel.CRITICAL: re.compile(
        r"\b(critical|fatal|panic|emerg)\b",
        re.I,
    ),

    LogLevel.ERROR: re.compile(
        r"(error|err|exception|traceback|failed|failure|doesnotexist|attributeerror|typeerror|valueerror|keyerror|indexerror|runtimeerror)",
        re.I,
    ),

    LogLevel.WARNING: re.compile(
        r"\b(warning|warn|deprecated)\b",
        re.I,
    ),

    LogLevel.DEBUG: re.compile(
        r"\b(debug|trace)\b",
        re.I,
    ),
}


def _detect_level(message: str) -> LogLevel:
    lowered = message.lower()

    if (
        "doesnotexist" in lowered
        or "traceback" in lowered
        or "exception" in lowered
        or "error" in lowered
    ):
        return LogLevel.ERROR

    for level, pattern in LEVEL_PATTERNS.items():
        if pattern.search(message):
            return level

    return LogLevel.INFO


def _build_docker_client(project: Project) -> docker.DockerClient:
    if project.docker_tls_enabled:
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = os.path.join(tmpdir, "cert.pem")
            key_path = os.path.join(tmpdir, "key.pem")
            ca_path = os.path.join(tmpdir, "ca.pem")

            if project.docker_tls_cert:
                with open(cert_path, "w") as f:
                    f.write(project.docker_tls_cert)
            if project.docker_tls_key:
                with open(key_path, "w") as f:
                    f.write(project.docker_tls_key)
            if project.docker_tls_ca:
                with open(ca_path, "w") as f:
                    f.write(project.docker_tls_ca)

            tls_config = docker.tls.TLSConfig(
                client_cert=(cert_path, key_path),
                ca_cert=ca_path if project.docker_tls_ca else None,
                verify=bool(project.docker_tls_ca),
            )
            return docker.DockerClient(base_url=project.docker_engine_url, tls=tls_config)
    else:
        return docker.DockerClient(base_url=project.docker_engine_url)


class DockerLogCollector:
    def __init__(self, project: Project, on_log_callback):
        self.project = project
        self.on_log = on_log_callback
        self._stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        
        
    async def start(self) -> None:
        logger.info(
        "DOCKER_COLLECTOR_START",
        project_id=str(self.project.id),
        )
        logger.info("docker_collector_start", project_id=str(self.project.id))
        client = await asyncio.get_event_loop().run_in_executor(
            None, _build_docker_client, self.project
        )
        containers = await self._list_containers(client)

        logger.info(
            "containers_found",
            count=len(containers),
            containers=[c.name for c in containers],
        )        
        for container in containers:
            print('CREATE TASK', container.name)
            task = asyncio.create_task(
                self._stream_container(client, container),
                name=f"docker:{self.project.id}:{container.name}",
            )
            self._tasks.append(task)

        asyncio.create_task(self._watch_new_containers(client))

    async def stop(self) -> None:
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()

    async def _list_containers(self, client: docker.DockerClient) -> list:
        filters = {"status": "running"}
        name_filter = self.project.docker_container_filter.get("name")
        if name_filter:
            filters["name"] = name_filter

        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.containers.list(filters=filters)
        )

    async def _watch_new_containers(self, client: docker.DockerClient) -> None:
        known = {t.get_name().split(":")[-1] for t in self._tasks}
        while not self._stop_event.is_set():
            await asyncio.sleep(3)
            try:
                containers = await self._list_containers(client)
                for c in containers:
                    if c.name not in known:
                        known.add(c.name)
                        task = asyncio.create_task(
                            self._stream_container(client, c),
                            name=f"docker:{self.project.id}:{c.name}",
                        )
                        self._tasks.append(task)
                        logger.info("new_container_attached", container=c.name)
            except Exception as e:
                logger.warning("container_watch_error", error=str(e))


    async def _stream_container(self, client: docker.DockerClient, container) -> None:
        
        container_name = container.name
        print("START STREAM", container_name)
        logger.warning(
            "ATTACHED_TO_CONTAINER",
            container=container_name,
        )
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        traceback_buffer = []
        collecting_traceback = False
        
        def _read_logs():
            try:
                log_gen = container.logs(stream=True, follow=True, timestamps=True, tail=0)
                for raw_line in log_gen:
                    if self._stop_event.is_set():
                        break
                    loop.call_soon_threadsafe(queue.put_nowait, raw_line)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, None)
                logger.error("container_read_error", container=container_name, error=str(e))

        loop.run_in_executor(None, _read_logs)

        try:
            while not self._stop_event.is_set():
                try:
                    raw_line = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if raw_line is None:
                    break

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                timestamp = datetime.now(timezone.utc)
                message = line
                if line[0].isdigit() and "Z " in line[:35]:
                    try:
                        ts_str, message = line.split(" ", 1)
                        timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                if "Traceback (most recent call last):" in message:
                    collecting_traceback = True
                    traceback_buffer = [message]
                    continue

                if collecting_traceback:
                    traceback_buffer.append(message)

                    if (
                        "Error:" in message
                        or "Exception" in message
                        or "DoesNotExist" in message
                    ):
                        message = "\n".join(traceback_buffer)
                        collecting_traceback = False
                    else:
                        continue

                level = _detect_level(message)
                raw_filter = self.project.log_level_filter or []
                filter_levels = [
                    l.value if hasattr(l, "value") else str(l)
                    for l in raw_filter
                ]
                should_store = (
                    not filter_levels
                    or level.value in filter_levels
                    or level in (LogLevel.ERROR, LogLevel.CRITICAL)
                )
                if not should_store:
                    continue

                entry = {
                    "project_id": str(self.project.id),
                    "source": LogSource.DOCKER.value,
                    "level": level.value,
                    "message": message[:4096],
                    "container_name": container_name,
                    "service_name": container.labels.get("com.docker.compose.service"),
                    "raw": {"line": line},
                    "timestamp": timestamp.isoformat(),
                }

                r = await get_redis()
                print('REDIS PUBLISH', entry)
                await r.publish(
                    f"project:{self.project.id}:logs",
                    json.dumps({"type": "log", "data": entry}, default=str)
                )
                print("LOG DETECTED")
                print(entry["container_name"])
                print(entry["message"][:200])
                await self.on_log(entry)

        except asyncio.CancelledError:
            logger.info("container_stream_cancelled", container=container_name)
        except Exception as e:
            logger.error("container_stream_error", container=container_name, error=str(e))