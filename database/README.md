# Database Setup (Supabase)

This folder contains schema files for the first phase only:
- Auth tables
- L0 tables
- L1 tables
- L2 tables

## Files
- `001_init_auth_l0_l2.sql`: create schema for `users`, `auth_sessions`, `books`, `source_files`, `chapters`, `chapter_extractions`
- `bootstrap.py`: apply SQL to remote PostgreSQL using a connection string

## Prerequisites
Install packages:

```bash
pip install supabase python-dotenv psycopg2-binary
```

## Option A: Run SQL in Supabase SQL Editor (recommended)
1. Open Supabase dashboard
2. Open SQL Editor
3. Paste `001_init_auth_l0_l2.sql`
4. Run it

## Option B: Apply from local machine
1. Add `.env` in project root with one of these variables:

```env
SUPABASE_DB_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
# or
DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
```

2. Run:

```bash
python database/bootstrap.py
```

## Notes
- This does NOT create L3 summary tables yet.
- Do NOT commit real keys/passwords into git.
- If credentials were exposed, rotate them in Supabase immediately.
