#! /usr/bin/env bash

echo "Running prestart.sh"
exec alembic upgrade head
echo "Finished prestart.sh"