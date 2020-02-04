CREATE TABLE `service_users`
(`id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
`login` VARCHAR(100) NOT NULL,
`password` VARCHAR(94))
);

CREATE TABLE `files`
(`id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
`fs_name` VARCHAR(255) NOT NULL,
`name` VARCHAR(255),
`visibility` BOOLEAN DEFAULT 0,
`description` TINYTEXT,
`owner` INT UNSIGNED NOT NULL,
FOREIGN KEY (`owner`) REFERENCES `service_users` (`id`)
);

CREATE TABLE `votes`(
`vote` TINYINT,
`voter` INT UNSIGNED NOT NULL,
`doc` INT UNSIGNED NOT NULL,
FOREIGN KEY (`voter`) REFERENCES `service_users`(`id`),
FOREIGN KEY (`doc`) REFERENCES `files`(`id`) ON DELETE CASCADE,
PRIMARY KEY(`voter`, `doc`)
);

CREATE VIEW sum_votes AS SELECT files.id fid, SUM(vote) votes FROM files INNER JOIN votes ON files.id = votes.doc GROUP BY files.id;

