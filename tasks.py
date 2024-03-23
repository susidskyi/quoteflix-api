import os

from invoke import task

WORKSPACE_MODE = os.environ.get("SOCIAL_WORKSPACE_MODE", "docker")


@task
def tests(ctx):
    ctx.run("docker compose run api-ops pytest app/tests")


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
def run_migrations(ctx):
    ctx.run("docker compose run api-ops alembic upgrade head")


@task
def setup(ctx):
    ctx.run("poetry install")
    ctx.run("poetry run pre-commit install")
    build(ctx)


@task
def format(ctx, path="app/api app/tests"):
    ctx.run(f"ruff {path}")
