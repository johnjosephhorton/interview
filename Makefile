.PHONY: install backend cli-chat cli-simulate test

install:
	pip install -e ".[cli,server,dev]"

backend:
	cd server && uvicorn app:create_app --factory --reload --port 8000

cli-chat:
	interview chat

cli-simulate:
	interview simulate

test:
	pytest
