.PHONY: install dev cli-chat cli-simulate frontend backend

install:
	pip install -e ".[cli,server,dev]"

dev: backend frontend

backend:
	cd server && uvicorn app:create_app --factory --reload --port 8000 &

frontend:
	cd frontend && npm run dev &

cli-chat:
	interview chat

cli-simulate:
	interview simulate

test:
	pytest
