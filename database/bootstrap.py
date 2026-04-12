import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    load_dotenv(root_dir / '.env')
    load_dotenv(Path(__file__).resolve().parent / '.env')

    database_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError(
            'Missing SUPABASE_DB_URL or DATABASE_URL in .env. '
            'Use a Postgres connection string, for example: '
            "postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require"
        )

    sql_path = Path(__file__).resolve().parent / '001_init_auth_l0_l2.sql'
    sql = sql_path.read_text(encoding='utf-8')

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print('Schema applied successfully: auth + L0 + L1 + L2')


if __name__ == '__main__':
    main()
