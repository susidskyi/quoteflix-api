from invoke import task

RUN_COMMAND = "docker compose -f docker-compose.yaml -f docker-compose.local.yaml"
RUN_TESTS_COMMAND = "docker compose -f docker-compose.tests.yaml"

@task(incrementable=["verbose"])
def tests(ctx, check_coverage=False, path="tests/", verbose=0):
    check_coverage_command = ""

    if check_coverage:
        check_coverage_command = "--cov  --cov-fail-under=90"

    command = (
        f"{RUN_TESTS_COMMAND} run --build api-test pytest --color=yes {check_coverage_command} {path} "
    )

    if verbose > 0:
        command += "-" + "v" * verbose

    ctx.run(
        command,
        pty=True,
    )


@task
def build(ctx):
    ctx.run(f"{RUN_COMMAND} build", pty=True)


@task
def run(ctx):
    ctx.run(f"{RUN_COMMAND} up", pty=True)


@task(help={"message": "Message string to use with 'revision'"})
def makemigrations(ctx, message):
    ctx.run(f"{RUN_COMMAND} run api alembic revision --autogenerate -m '{message}'")


@task
def mypy(ctx):
    ctx.run("mypy app/", pty=True)


@task
def checks(ctx):
    mypy(ctx)


@task
def ci(ctx):
    checks(ctx)
    tests(ctx, check_coverage=True)


@task
def checks(ctx):
    mypy(ctx)


@task
def ci(ctx):
    checks(ctx)
    tests(ctx, check_coverage=True)


@task
def migrate(ctx):
    ctx.run(f"{RUN_COMMAND} run api alembic upgrade head", pty=True)


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
