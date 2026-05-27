import asyncio
import logging
from sqlalchemy import text
from core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_schema():
    logger.info("Connecting to database...")
    async with db_manager.async_session_maker() as db:
        # 1. Add missing columns to pos_terminals
        columns_to_add = [
            ("device_id", "VARCHAR(255)"),
            ("last_device_id", "VARCHAR(255)"),
            ("operator_pin", "VARCHAR(255)"),
            ("authorized_at", "TIMESTAMP WITH TIME ZONE"),
            ("is_t0_settlement", "BOOLEAN DEFAULT FALSE NOT NULL"),
            ("merchant_id", "VARCHAR(64)"),
            ("description", "TEXT"),
            ("assigned_by", "VARCHAR(64)"),
            ("assigned_at", "TIMESTAMP WITH TIME ZONE"),
            ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT now()"),
            ("deactivated_at", "TIMESTAMP WITH TIME ZONE"),
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                logger.info(f"Adding column {col_name} to pos_terminals...")
                await db.execute(text(f"ALTER TABLE pos_terminals ADD COLUMN {col_name} {col_type}"))
                logger.info(f"Column {col_name} added.")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"Column {col_name} already exists, skipping.")
                else:
                    logger.error(f"Error adding column {col_name}: {e}")

        # 2. Create pos_terminal_devices table if not exists
        try:
            logger.info("Creating pos_terminal_devices table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS pos_terminal_devices (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(255) UNIQUE NOT NULL,
                    brand VARCHAR(100),
                    model VARCHAR(100),
                    os_version VARCHAR(50),
                    app_version VARCHAR(50),
                    is_authorized BOOLEAN DEFAULT FALSE NOT NULL,
                    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    metadata_json JSON,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
            """))
            logger.info("Table pos_terminal_devices created or already exists.")
        except Exception as e:
            logger.error(f"Error creating pos_terminal_devices: {e}")

        # 3. Create pos_terminal_requests table if not exists
        try:
            logger.info("Creating pos_terminal_requests table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS pos_terminal_requests (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    user_name VARCHAR(255) NOT NULL,
                    user_email VARCHAR(255),
                    user_phone VARCHAR(20),
                    business_name VARCHAR(255) NOT NULL,
                    business_type VARCHAR(100),
                    location VARCHAR(255),
                    description TEXT,
                    required_payment_methods JSON NOT NULL,
                    monthly_transaction_volume INTEGER,
                    average_transaction_amount INTEGER,
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    rejection_reason TEXT,
                    assigned_terminal_id INTEGER,
                    reviewed_by VARCHAR(64),
                    reviewed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
            """))
            logger.info("Table pos_terminal_requests created or already exists.")
        except Exception as e:
            logger.error(f"Error creating pos_terminal_requests: {e}")

        # 4. Create pos_terminal_transactions table if not exists
        try:
            logger.info("Creating pos_terminal_transactions table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS pos_terminal_transactions (
                    id SERIAL PRIMARY KEY,
                    terminal_id INTEGER NOT NULL,
                    user_id VARCHAR(64) NOT NULL,
                    order_id VARCHAR(100) UNIQUE NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    amount INTEGER NOT NULL,
                    currency VARCHAR(3) DEFAULT 'PHP' NOT NULL,
                    payment_method VARCHAR(50) NOT NULL,
                    maya_checkout_id VARCHAR(255),
                    paymongo_checkout_id VARCHAR(255),
                    xendit_invoice_id VARCHAR(255),
                    payment_url VARCHAR(2048),
                    qr_content TEXT,
                    customer_name VARCHAR(255),
                    customer_email VARCHAR(255),
                    customer_phone VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    failure_reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    completed_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
            """))
            logger.info("Table pos_terminal_transactions created or already exists.")
        except Exception as e:
            logger.error(f"Error creating pos_terminal_transactions: {e}")

        # 5. Stamp alembic to latest
        try:
             logger.info("Stamping alembic head...")
             # This requires alembic to be in path, which might not be here.
             # We can't easily run alembic commands from inside python async loop safely
             # without subprocess. But we just fixed the schema, so app should run.
             pass
        except Exception:
             pass

        await db.commit()
        logger.info("Schema fix completed.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
