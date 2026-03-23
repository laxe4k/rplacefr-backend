import warnings
import aiomysql
from contextlib import asynccontextmanager
from app.config import get_settings

# Ignorer les warnings "Table already exists" de aiomysql
warnings.filterwarnings("ignore", category=Warning, module="aiomysql")

settings = get_settings()

# Pool de connexions
pool: aiomysql.Pool | None = None


async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_pass,
        db=settings.db_name,
        charset="utf8mb4",
        autocommit=True,
        minsize=1,
        maxsize=10,
    )


async def close_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()


@asynccontextmanager
async def get_connection():
    global pool
    if pool is None:
        await create_pool()
    assert pool is not None
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            yield cursor


async def init_database():
    """Crée les tables si elles n'existent pas."""
    async with get_connection() as cursor:
        # Table users
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `users` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `username` varchar(255) NOT NULL UNIQUE,
                `password_hash` varchar(255) NOT NULL,
                `is_admin` tinyint(1) NOT NULL DEFAULT 0,
                `is_approved` tinyint(1) NOT NULL DEFAULT 0,
                `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        )

        # Migration: ajouter is_approved si la colonne n'existe pas encore
        try:
            await cursor.execute(
                "ALTER TABLE `users` ADD COLUMN `is_approved` tinyint(1) NOT NULL DEFAULT 0"
            )
        except Exception:
            pass  # La colonne existe déjà

        # Approuver automatiquement tous les admins existants
        await cursor.execute(
            "UPDATE `users` SET `is_approved` = 1 WHERE `is_admin` = 1"
        )

        # Table options
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `options` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `event` tinyint(1) NOT NULL DEFAULT 0,
                `clientId` varchar(255) DEFAULT NULL,
                `clientSecret` varchar(255) DEFAULT NULL,
                `oauth_token` text DEFAULT NULL,
                `token_expires_at` bigint(20) DEFAULT 0,
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        )

        # Table links
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `links` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `discord` varchar(255) DEFAULT '',
                `reddit` varchar(255) DEFAULT '',
                `tuto` varchar(255) DEFAULT '',
                `atlas` varchar(255) DEFAULT '',
                `relations` varchar(255) DEFAULT '',
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        )

        # Table streamers
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS `streamers` (
                `id` int(11) DEFAULT NULL,
                `name` varchar(255) NOT NULL,
                PRIMARY KEY (`name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        )

        # Insérer les données par défaut si elles n'existent pas
        await cursor.execute("SELECT COUNT(*) as count FROM options")
        result = await cursor.fetchone()
        if result["count"] == 0:
            await cursor.execute("INSERT INTO options (id, event) VALUES (1, 0)")

        await cursor.execute("SELECT COUNT(*) as count FROM links")
        result = await cursor.fetchone()
        if result["count"] == 0:
            await cursor.execute(
                """INSERT INTO links (id, discord, reddit, tuto, atlas, relations) 
                VALUES (1, '', '', '', '', '')"""
            )

        # Insérer les données par défaut si elles n'existent pas
        await cursor.execute("SELECT COUNT(*) as count FROM options")
        result = await cursor.fetchone()
        if result["count"] == 0:
            await cursor.execute("INSERT INTO options (id, event) VALUES (1, 0)")

        await cursor.execute("SELECT COUNT(*) as count FROM links")
        result = await cursor.fetchone()
        if result["count"] == 0:
            await cursor.execute(
                "INSERT INTO links (id, discord, reddit, atlas) VALUES (1, '', '', '')"
            )

        print("Base de données initialisée avec succès")
