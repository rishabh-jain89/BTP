#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-btp_eval}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

export PGPASSWORD="$DB_PASSWORD"

echo "Stopping old temporary job/output folders..."
rm -rf \
  "$DATA_DIR/assignments" \
  "$DATA_DIR/temp_jplag" \
  "$DATA_DIR/jplag_reports" \
  "$DATA_DIR/tmp_jobs"

mkdir -p "$DATA_DIR"

echo "Resetting PostgreSQL tables..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<'SQL'
TRUNCATE TABLE
    adhoc_question_results,
    submission_question_results,
    assignment_questions,
    plagiarism_results,
    execution_runs,
    evaluation_results,
    evaluation_jobs,
    submissions,
    test_cases,
    students,
    assignments
RESTART IDENTITY CASCADE;
SQL

echo "Reset complete."
echo "Now restart:"
echo "  1. FastAPI server"
echo "  2. evaluation worker"
echo "  3. plagiarism worker"
echo "  4. question worker"