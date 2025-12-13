-- Schema for reminder tasks used by recruitment reminders
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reminder_task_status') THEN
        CREATE TYPE reminder_task_status AS ENUM ('pending', 'done', 'ignored');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reminder_task_type') THEN
        CREATE TYPE reminder_task_type AS ENUM ('message', 'candidate', 'job_update', 'interview', 'other');
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS reminder_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employer_id UUID NOT NULL,
    job_id UUID NULL,
    candidate_id UUID NULL,
    task_title VARCHAR(255) NOT NULL,
    task_type reminder_task_type NOT NULL,
    redirect_url VARCHAR(1024) NOT NULL,
    due_at TIMESTAMPTZ NULL,
    status reminder_task_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_reminder_tasks_employer_status ON reminder_tasks (employer_id, status);
CREATE INDEX IF NOT EXISTS ix_reminder_tasks_due_at ON reminder_tasks (due_at);
