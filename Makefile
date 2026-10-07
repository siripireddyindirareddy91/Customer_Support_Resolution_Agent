.PHONY: install api test lint

install:
	pip install -r requirements.txt

api:
	uvicorn backend.app.main:app --reload

test:
	pytest

lint:
	ruff check backend ai tests