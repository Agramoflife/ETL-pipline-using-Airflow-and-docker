#!/usr/bin/env python3
"""
Automated Incremental RDS to On-Premise Database Migration Script (Using last_ingested_id)
"""

import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sshtunnel import SSHTunnelForwarder
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        # SSH Tunnel Configuration
        self.ssh_config = {
            'ssh_host': os.getenv('SSH_HOST'),
            'ssh_port': int(os.getenv('SSH_PORT')),
            'ssh_username': os.getenv('SSH_USERNAME'),
            'ssh_key_path': os.getenv('SSH_KEY_PATH')
        }

        # RDS Configuration
        self.rds_config = {
            'host': os.getenv('RDS_HOST'),
            'port': int(os.getenv('RDS_PORT')),
            'database': os.getenv('RDS_DATABASE'),
            'user': os.getenv('RDS_USER'),
            'password': os.getenv('RDS_PASSWORD')
        }

        # On-Premise Configuration
        self.onprem_config = {
            'host': os.getenv('ONPREM_HOST'),
            'port': int(os.getenv('ONPREM_PORT')),
            'database': os.getenv('ONPREM_DATABASE'),
            'user': os.getenv('ONPREM_USER'),
            'password': os.getenv('ONPREM_PASSWORD')
        }

        self.batch_size = int(os.getenv('BATCH_SIZE', 10000))
        self.tables_to_migrate = os.getenv('TABLES_TO_MIGRATE').split(',')

        self.tunnel = None
        self.rds_engine = None
        self.onprem_engine = None

    def setup_ssh_tunnel(self):
        try:
            logger.info("Setting up SSH tunnel...")
            self.tunnel = SSHTunnelForwarder(
                (self.ssh_config['ssh_host'], self.ssh_config['ssh_port']),
                ssh_username=self.ssh_config['ssh_username'],
                ssh_pkey=self.ssh_config['ssh_key_path'],
                remote_bind_address=(self.rds_config['host'], self.rds_config['port']),
                local_bind_address=('localhost', 5434)
            )
            self.tunnel.start()
            logger.info(f"SSH tunnel established on local port {self.tunnel.local_bind_port}")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed to setup SSH tunnel: {e}")
            return False

    def create_database_connections(self):
        try:
            rds_url = f"postgresql+psycopg2://{self.rds_config['user']}:{self.rds_config['password']}@localhost:{self.tunnel.local_bind_port}/{self.rds_config['database']}"
            self.rds_engine = create_engine(rds_url, pool_pre_ping=True)

            onprem_url = f"postgresql+psycopg2://{self.onprem_config['user']}:{self.onprem_config['password']}@{self.onprem_config['host']}:{self.onprem_config['port']}/{self.onprem_config['database']}"
            self.onprem_engine = create_engine(onprem_url, pool_pre_ping=True)

            self.rds_engine.connect().execute(text("SELECT 1"))
            self.onprem_engine.connect().execute(text("SELECT 1"))
            logger.info("Database connections successful")
            return True
        except Exception as e:
            logger.error(f"Failed to create database connections: {e}")
            return False

    # this basicall gets the last ingested id from the destination tables
    def get_last_ingested_id(self, table_name):
        try:
            with self.onprem_engine.connect() as conn:
                result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to fetch last ingested ID from destination for {table_name}: {e}")
            return 0

    def migrate_table_incrementally(self, table_name):
        try:
            logger.info(f"Starting incremental migration for table: {table_name}")
            last_ingested_id = self.get_last_ingested_id(table_name)
            logger.info(f"Last ingested ID for {table_name}: {last_ingested_id}")

            migrated_rows = 0

            while True:
                query = text(f"""
                    SELECT * FROM {table_name}
                    WHERE id > :last_id
                    ORDER BY id ASC
                    LIMIT :batch
                """)

                df = pd.read_sql(query, self.rds_engine, params={
                    'last_id': int(last_ingested_id), # deepu you will have to convert this into int this is a type cast error
                    'batch': int(self.batch_size)
                })

                if df.empty:
                    break

                df.to_sql(table_name, self.onprem_engine, if_exists='append', index=False, method='multi')

                last_ingested_id = df['id'].max()
                migrated_rows += len(df)
                logger.info(f"Migrated {migrated_rows} rows so far for {table_name} (last ID: {last_ingested_id})")

            logger.info(f"Finished migrating table {table_name} | Total rows migrated: {migrated_rows}")
            return True

        except Exception as e:
            logger.error(f"Error migrating table {table_name} incrementally: {e}")
            return False

    def cleanup(self):
        try:
            if self.rds_engine:
                self.rds_engine.dispose()
            if self.onprem_engine:
                self.onprem_engine.dispose()
            if self.tunnel:
                self.tunnel.stop()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run_migration(self):
        try:
            logger.info("Starting incremental database migration process...")
            if not self.setup_ssh_tunnel():
                return False
            if not self.create_database_connections():
                return False

            success_tables = []
            failed_tables = []

            for table in self.tables_to_migrate:
                table = table.strip()
                logger.info(f"Processing table: {table}")
                if self.migrate_table_incrementally(table):
                    success_tables.append(table)
                else:
                    failed_tables.append(table)

            logger.info(f"Migration completed | Success: {success_tables} | Failed: {failed_tables}")
            return len(failed_tables) == 0

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    sys.exit(0 if success else 1)
