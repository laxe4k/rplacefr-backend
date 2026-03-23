-- SQL pour créer les tables nécessaires pour le backend
CREATE TABLE
    IF NOT EXISTS `options` (
        `id` int (11) NOT NULL AUTO_INCREMENT,
        `event` tinyint (1) NOT NULL DEFAULT 0,
        `clientId` varchar(255) DEFAULT NULL,
        `clientSecret` varchar(255) DEFAULT NULL,
        `oauth_token` text DEFAULT NULL,
        `token_expires_at` bigint (20) DEFAULT 0,
        PRIMARY KEY (`id`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS `links` (
        `id` int (11) NOT NULL AUTO_INCREMENT,
        `discord` varchar(255) DEFAULT '',
        `reddit` varchar(255) DEFAULT '',
        `tuto` varchar(255) DEFAULT '',
        `atlas` varchar(255) DEFAULT '',
        `relations` varchar(255) DEFAULT '',
        PRIMARY KEY (`id`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS `streamers` (
        `id` int (11) DEFAULT NULL,
        `name` varchar(255) NOT NULL,
        PRIMARY KEY (`name`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS `users` (
        `id` int (11) NOT NULL AUTO_INCREMENT,
        `username` varchar(255) NOT NULL UNIQUE,
        `password_hash` varchar(255) NOT NULL,
        `is_admin` tinyint (1) NOT NULL DEFAULT 0,
        `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- Insérer les données par défaut
INSERT INTO
    `options` (`id`, `event`)
VALUES
    (1, 0) ON DUPLICATE KEY
UPDATE id = id;

INSERT INTO
    `links` (`id`, `discord`, `reddit`, `atlas`)
VALUES
    (1, '', '', '') ON DUPLICATE KEY
UPDATE id = id;