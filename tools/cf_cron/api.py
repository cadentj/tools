"""Cloudflare cron management primitives for Hermes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import re
import time
from typing import Any
from urllib import error, request
import uuid


DEFAULT_WORKER_NAME = "hermes-cron"
DEFAULT_JOBS_PATH = Path("/data/repos/tools/projects/agent/jobs.md")
SYNTHETIC_PREFIX = "\N{ALARM CLOCK}"
_HEADING_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")
_FIELD_RE = re.compile(r"^-\s*(?P<key>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.+?)\s*$")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


class CronConfigError(ValueError):
    """Raised when local cron configuration is invalid."""


@dataclass(frozen=True)
class Job:
    name: str
    slug: str
    cron: str
    enabled: bool
    description: str


@dataclass(frozen=True)
class CloudflareConfig:
    account_id: str
    api_token: str
    worker_name: str = DEFAULT_WORKER_NAME


@dataclass(frozen=True)
class HermesTriggerConfig:
    webhook_url: str
    webhook_secret: str
    trigger_user_id: int
    jobs_path: Path


def build_jobs_file_template() -> str:
    return (
        "# Hermes Cron Jobs\n\n"
        "Each job starts with a level-2 heading. Hermes receives messages in the form\n"
        f"`{SYNTHETIC_PREFIX} Job Name` and should look up the matching heading here.\n\n"
        "## Morning Check-In\n"
        "- cron: 0 13 * * *\n"
        "- enabled: true\n\n"
        "Review overnight messages, summarize anything urgent, and prepare the first\n"
        "reply you should send.\n"
    )


def slugify(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    if not slug:
        raise CronConfigError(f"unable to derive slug from job name: {name!r}")
    return slug


def _parse_bool(raw: str, *, field: str, job_name: str) -> bool:
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise CronConfigError(f"{job_name}: invalid {field} value {raw!r}")


def _build_job(name: str, field_lines: list[str], description_lines: list[str]) -> Job:
    if not field_lines:
        raise CronConfigError(f"{name}: missing metadata block")

    fields: dict[str, str] = {}
    for line in field_lines:
        match = _FIELD_RE.match(line)
        if not match:
            raise CronConfigError(f"{name}: invalid metadata line {line!r}")
        key = match.group("key").strip().lower()
        value = match.group("value").strip()
        if key in fields:
            raise CronConfigError(f"{name}: duplicate metadata field {key!r}")
        fields[key] = value

    cron = fields.get("cron")
    if not cron:
        raise CronConfigError(f"{name}: missing cron field")

    enabled = _parse_bool(fields.get("enabled", "true"), field="enabled", job_name=name)
    description = "\n".join(description_lines).strip()
    if not description:
        raise CronConfigError(f"{name}: missing description")

    return Job(
        name=name,
        slug=slugify(name),
        cron=cron,
        enabled=enabled,
        description=description,
    )


def parse_jobs_markdown(text: str) -> list[Job]:
    jobs: list[Job] = []
    current_name: str | None = None
    field_lines: list[str] = []
    description_lines: list[str] = []
    in_description = False

    for raw_line in text.splitlines():
        heading = _HEADING_RE.match(raw_line)
        if heading:
            if current_name is not None:
                jobs.append(_build_job(current_name, field_lines, description_lines))
            current_name = heading.group("name").strip()
            field_lines = []
            description_lines = []
            in_description = False
            continue

        if current_name is None:
            continue

        if not in_description:
            if not raw_line.strip():
                if field_lines:
                    in_description = True
                continue
            if raw_line.lstrip().startswith("- "):
                field_lines.append(raw_line.strip())
                continue
            raise CronConfigError(f"{current_name}: description must come after a blank line")

        description_lines.append(raw_line)

    if current_name is not None:
        jobs.append(_build_job(current_name, field_lines, description_lines))

    if not jobs:
        raise CronConfigError("no jobs found in jobs.md")

    seen_names: set[str] = set()
    seen_slugs: set[str] = set()
    for job in jobs:
        lower_name = job.name.lower()
        if lower_name in seen_names:
            raise CronConfigError(f"duplicate job name: {job.name}")
        if job.slug in seen_slugs:
            raise CronConfigError(f"duplicate job slug: {job.slug}")
        seen_names.add(lower_name)
        seen_slugs.add(job.slug)
    return jobs


def load_jobs(path: Path) -> list[Job]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CronConfigError(f"jobs file not found: {path}") from exc
    return parse_jobs_markdown(text)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise CronConfigError(f"missing required environment variable: {name}")
    return value


def load_runtime_config() -> tuple[Path, CloudflareConfig, HermesTriggerConfig]:
    jobs_path = Path(os.environ.get("HERMES_CRON_JOBS_FILE", str(DEFAULT_JOBS_PATH))).expanduser()
    allowed_users = _required_env("TELEGRAM_ALLOWED_USERS")
    trigger_raw = os.environ.get("HERMES_CRON_TRIGGER_USER_ID", "").strip() or allowed_users.split(",")[0].strip()
    try:
        trigger_user_id = int(trigger_raw)
    except ValueError as exc:
        raise CronConfigError(f"invalid trigger user id: {trigger_raw!r}") from exc

    cloudflare = CloudflareConfig(
        account_id=_required_env("CLOUDFLARE_ACCOUNT_ID"),
        api_token=_required_env("CLOUDFLARE_API_TOKEN"),
        worker_name=os.environ.get("CLOUDFLARE_WORKER_NAME", DEFAULT_WORKER_NAME).strip() or DEFAULT_WORKER_NAME,
    )
    hermes = HermesTriggerConfig(
        webhook_url=_required_env("TELEGRAM_WEBHOOK_URL"),
        webhook_secret=_required_env("TELEGRAM_WEBHOOK_SECRET"),
        trigger_user_id=trigger_user_id,
        jobs_path=jobs_path,
    )
    return jobs_path, cloudflare, hermes


def _json_request(
    url: str,
    *,
    method: str,
    api_token: str,
    payload: Any | None = None,
    content_type: str = "application/json",
) -> dict[str, Any]:
    data: bytes | None = None
    if payload is not None:
        if content_type == "application/json":
            data = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, bytes):
            data = payload
        else:
            raise TypeError("non-JSON payload must be bytes")

    req = request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": content_type,
        },
    )
    try:
        with request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare API error {exc.code}: {body}") from exc
    return json.loads(body) if body else {}


def _multipart_form(parts: list[tuple[str, str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----cfcron-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for field_name, filename, content, mime_type in parts:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        disposition = f'Content-Disposition: form-data; name="{field_name}"'
        if filename:
            disposition += f'; filename="{filename}"'
        chunks.append(f"{disposition}\r\n".encode("utf-8"))
        chunks.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        chunks.append(content)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


class CloudflareClient:
    def __init__(self, config: CloudflareConfig) -> None:
        self.config = config

    def _script_url(self, suffix: str = "") -> str:
        base = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.config.account_id}/workers/scripts/{self.config.worker_name}"
        )
        return f"{base}{suffix}"

    def upload_worker(self, source: str, jobs_by_cron: dict[str, list[str]], trigger_user_id: int) -> dict[str, Any]:
        metadata = {
            "main_module": "worker.js",
            "compatibility_date": date.today().isoformat(),
            "bindings": [
                {
                    "type": "plain_text",
                    "name": "JOBS_BY_CRON_JSON",
                    "text": json.dumps(jobs_by_cron, sort_keys=True),
                },
                {
                    "type": "plain_text",
                    "name": "HERMES_TRIGGER_USER_ID",
                    "text": str(trigger_user_id),
                },
            ],
        }
        body, content_type = _multipart_form(
            [
                ("metadata", "", json.dumps(metadata).encode("utf-8"), "application/json"),
                ("worker.js", "worker.js", source.encode("utf-8"), "application/javascript+module"),
            ]
        )
        return _json_request(
            self._script_url(),
            method="PUT",
            api_token=self.config.api_token,
            payload=body,
            content_type=content_type,
        )

    def put_secret(self, name: str, value: str) -> dict[str, Any]:
        payload = {"name": name, "text": value, "type": "secret_text"}
        return _json_request(
            self._script_url("/secrets"),
            method="PUT",
            api_token=self.config.api_token,
            payload=payload,
        )

    def replace_schedules(self, schedules: list[dict[str, Any]]) -> dict[str, Any]:
        return _json_request(
            self._script_url("/schedules"),
            method="PUT",
            api_token=self.config.api_token,
            payload=schedules,
        )

    def list_schedules(self) -> list[dict[str, Any]]:
        response = _json_request(
            self._script_url("/schedules"),
            method="GET",
            api_token=self.config.api_token,
        )
        return list(response.get("result") or [])


def build_jobs_by_cron(jobs: list[Job]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for job in jobs:
        if not job.enabled:
            continue
        grouped.setdefault(job.cron, []).append(job.name)
    return {cron: sorted(names) for cron, names in sorted(grouped.items())}


def build_schedule_payloads(jobs: list[Job]) -> list[dict[str, Any]]:
    jobs_by_cron = build_jobs_by_cron(jobs)
    return [
        {
            "cron": cron,
            "body": {"job_names": names},
        }
        for cron, names in jobs_by_cron.items()
    ]


def render_worker_source() -> str:
    return """export default {
  async scheduled(controller, env, ctx) {
    const jobsByCron = JSON.parse(env.JOBS_BY_CRON_JSON || "{}");
    const names = jobsByCron[controller.cron] || [];
    for (const name of names) {
      ctx.waitUntil(triggerHermes(env, name));
    }
  },
  async fetch(_request, env) {
    const jobsByCron = JSON.parse(env.JOBS_BY_CRON_JSON || "{}");
    return Response.json({
      ok: true,
      worker: "hermes-cron",
      cron_count: Object.keys(jobsByCron).length,
    });
  },
};

async function triggerHermes(env, jobName) {
  const now = Math.floor(Date.now() / 1000);
  const userId = Number(env.HERMES_TRIGGER_USER_ID);
  const payload = {
    update_id: now,
    message: {
      message_id: now,
      date: now,
      text: `⏰ ${jobName}`,
      from: {
        id: userId,
        is_bot: false,
        first_name: "Cron",
        username: "cloudflare_cron",
      },
      chat: {
        id: userId,
        type: "private",
        first_name: "Cron",
      },
    },
  };

  const response = await fetch(env.TELEGRAM_WEBHOOK_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-telegram-bot-api-secret-token": env.TELEGRAM_WEBHOOK_SECRET,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Hermes webhook failed: ${response.status} ${body}`);
  }
}
"""


def sync_worker(client: CloudflareClient, hermes: HermesTriggerConfig, jobs: list[Job]) -> dict[str, Any]:
    jobs_by_cron = build_jobs_by_cron(jobs)
    client.upload_worker(render_worker_source(), jobs_by_cron, hermes.trigger_user_id)
    client.put_secret("TELEGRAM_WEBHOOK_URL", hermes.webhook_url)
    client.put_secret("TELEGRAM_WEBHOOK_SECRET", hermes.webhook_secret)
    client.replace_schedules(build_schedule_payloads(jobs))
    return {"schedule_count": len(jobs_by_cron)}


def find_job(jobs: list[Job], job_name_or_slug: str) -> Job:
    needle = job_name_or_slug.strip().lower()
    for job in jobs:
        if job.slug == needle or job.name.lower() == needle:
            return job
    raise CronConfigError(f"unknown job: {job_name_or_slug}")


def _synthetic_update(job: Job, hermes: HermesTriggerConfig) -> dict[str, Any]:
    stamp = int(time.time())
    return {
        "update_id": stamp,
        "message": {
            "message_id": stamp,
            "date": stamp,
            "text": f"{SYNTHETIC_PREFIX} {job.name}",
            "from": {
                "id": hermes.trigger_user_id,
                "is_bot": False,
                "first_name": "Cron",
                "username": "cloudflare_cron",
            },
            "chat": {
                "id": hermes.trigger_user_id,
                "type": "private",
                "first_name": "Cron",
            },
        },
    }


def send_synthetic_update(hermes: HermesTriggerConfig, job: Job) -> None:
    payload = json.dumps(_synthetic_update(job, hermes)).encode("utf-8")
    req = request.Request(
        hermes.webhook_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Telegram-Bot-Api-Secret-Token": hermes.webhook_secret,
        },
    )
    try:
        with request.urlopen(req):
            return
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hermes webhook error {exc.code}: {body}") from exc


def trigger_job(hermes: HermesTriggerConfig, jobs: list[Job], job_name_or_slug: str) -> Job:
    job = find_job(jobs, job_name_or_slug)
    send_synthetic_update(hermes, job)
    return job
