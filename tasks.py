import os

from invoke import task

WORKSPACE_MODE = os.environ.get("SOCIAL_WORKSPACE_MODE", "docker")


@task
def tests(ctx, path="app/"):
    ctx.run(f"docker compose run api-ops pytest {path}", pty=True)


@task
def build(ctx):
    ctx.run("docker compose build")


@task
def run(ctx):
    ctx.run("docker compose up")


@task(help={"message": "Message string to use with 'revision'"})
def makemigrations(ctx, message):
    ctx.run(
        f"docker compose run api-ops alembic revision --autogenerate -m '{message}'"
    )


@task
def migrate(ctx):
    ctx.run("docker compose run api-ops alembic upgrade head")


@task
def setup(ctx):
    ctx.run("poetry install")
    ctx.run("poetry run pre-commit install")
    ctx.run("cp .env.example .env")
    build(ctx)


@task
def format(ctx, path="app/"):
    ctx.run(f"ruff format {path}")
    ctx.run(f"ruff check --select I --fix {path}")
