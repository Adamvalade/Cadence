Cadence is a social app for logging albums, rating/reviewing music, and discovering new releases through people you follow.


Cadence/
  api/
    app/
      main.py
      core/        # settings, security, logging
      db/          # engine/session, base
      models/      # SQLAlchemy models
      schemas/     # Pydantic DTOs
      routers/     # FastAPI routers
      services/    # spotify client, feed builder, etc.
      tasks/       # background jobs (optional)
    tests/
    alembic/
    requirements.txt (or pyproject.toml)
  web/
    src/
      pages/ or app/   # if Next
      components/
      lib/             # api client, auth helpers
      styles/
  bin/
    setup.sh
  docker-compose.yml
  README.md
  SPEC.md