from invoke import task


@task(incrementable=["verbose"], optional=["check_coverage", "path"])
def tests(ctx, check_coverage=False, path="app/", verbose=0):
    check_coverage_command = ""

    if check_coverage:
        check_coverage_command = "--cov  --cov-fail-under=85"

    command = f"docker compose run api-ops pytest --color=yes {check_coverage_command} {path} "

    if verbose > 0:
        command += "-" + "v" * verbose

    ctx.run(
        command,
        pty=True,
    )


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
def checks(ctx):
    ctx.run("mypy app/", pty=True)


@task
def ci(ctx):
    checks(ctx)
    tests(ctx, check_coverage=True)


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
