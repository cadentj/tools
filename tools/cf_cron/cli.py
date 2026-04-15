"""Cloudflare cron management CLI for Hermes."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from tools.cf_cron.api import (
    CloudflareClient,
    CloudflareConfig,
    CronConfigError,
    HermesTriggerConfig,
    build_jobs_file_template,
    load_jobs,
    load_runtime_config,
    sync_worker,
    trigger_job,
)
from tools.cf_cron.help import (
    APP_HELP,
    INIT_HELP,
    LIST_HELP,
    SYNC_HELP,
    TRIGGER_HELP,
    VALIDATE_HELP,
)

app = typer.Typer(help=APP_HELP, no_args_is_help=True)


def _load_all() -> tuple[Path, CloudflareConfig, HermesTriggerConfig]:
    jobs_path, cloudflare, hermes = load_runtime_config()
    return jobs_path, cloudflare, hermes


@app.command("init", help=INIT_HELP)
def cmd_init(force: bool = typer.Option(False, "--force", help="Overwrite an existing jobs file.")) -> None:
    jobs_path, _, _ = _load_all()
    if jobs_path.exists() and not force:
        raise typer.BadParameter(f"jobs file already exists: {jobs_path}")
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(build_jobs_file_template(), encoding="utf-8")
    typer.echo(f"Initialized {jobs_path}")


@app.command("validate", help=VALIDATE_HELP)
def cmd_validate() -> None:
    jobs_path, _, _ = _load_all()
    jobs = load_jobs(jobs_path)
    typer.echo(f"{jobs_path}: {len(jobs)} valid job(s)")


@app.command("list", help=LIST_HELP)
def cmd_list(remote: bool = typer.Option(False, "--remote", help="Also show remote Cloudflare schedules.")) -> None:
    jobs_path, cloudflare, _ = _load_all()
    jobs = load_jobs(jobs_path)
    typer.echo(f"Local jobs from {jobs_path}:")
    for job in jobs:
        status = "enabled" if job.enabled else "disabled"
        typer.echo(f"- {job.slug}: {job.name} [{job.cron}] ({status})")

    if not remote:
        return

    client = CloudflareClient(cloudflare)
    schedules = client.list_schedules()
    typer.echo("")
    typer.echo(f"Remote schedules for {cloudflare.worker_name}:")
    for schedule in schedules:
        payload = schedule.get("body") or {}
        summary = json.dumps(payload, sort_keys=True) if payload else "{}"
        typer.echo(f"- {schedule['cron']}: {summary}")


@app.command("sync", help=SYNC_HELP)
def cmd_sync() -> None:
    jobs_path, cloudflare, hermes = _load_all()
    jobs = load_jobs(jobs_path)
    client = CloudflareClient(cloudflare)
    summary = sync_worker(client, hermes, jobs)
    typer.echo(
        f"Synced {len(jobs)} job(s) to worker {cloudflare.worker_name}: "
        f"{summary['schedule_count']} schedule(s)"
    )


@app.command("trigger", help=TRIGGER_HELP)
def cmd_trigger(job_name_or_slug: str = typer.Argument(..., help="Job slug or exact job name.")) -> None:
    jobs_path, _, hermes = _load_all()
    jobs = load_jobs(jobs_path)
    job = trigger_job(hermes, jobs, job_name_or_slug)
    typer.echo(f"Triggered {job.name}")


def main() -> None:
    try:
        app()
    except (CronConfigError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    main()
