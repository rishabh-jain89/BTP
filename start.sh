#!/bin/bash

gnome-terminal -- bash -c "celery -A workers.evaluation_tasks worker -Q evaluation_queue --concurrency=1 --loglevel=info; exec bash"

gnome-terminal -- bash -c "celery -A workers.plagiarism_tasks worker -Q plagiarism_queue --concurrency=1 --loglevel=info; exec bash"

gnome-terminal -- bash -c "celery -A workers.question_tasks worker -Q question_queue --concurrency=1 --loglevel=info; exec bash"

gnome-terminal -- bash -c "uvicorn api.main:app --reload; exec bash"

gnome-terminal -- bash -c "cd frontend && npm run dev; exec bash"