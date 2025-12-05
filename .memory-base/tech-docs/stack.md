technologies:
	python >= 3.13
	postgres 17
	alembic >= 1.17.0
	kafka
	redis
	typescript
	vite
	react


libs for python:

	prod:
		# async message broker
		faststream >= 0.6.3

		# web framework
		fastapi >= 0.120.0
		uvicorn >= 0.38.0

		# data validation
		pydantic >= 2.12.0

		# database
		sqlalchemy >= 2.0.44, async
		asyncpg >= 0.31.0  # async PostgreSQL driver

	dev deps:
		mypy >= 1.19.0
		ruff >= 0.14.0


sources:
	https://pypi.org/project/faststream/
	https://pypi.org/project/fastapi/
	https://pypi.org/project/uvicorn/
	https://pypi.org/project/pydantic/
	https://pypi.org/project/SQLAlchemy/
	https://pypi.org/project/asyncpg/
	https://pypi.org/project/alembic/
	https://pypi.org/project/mypy/
	https://pypi.org/project/ruff/




