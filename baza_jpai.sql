-- phpMyAdmin SQL Dump
-- version 5.0.4deb2+deb11u1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Czas generowania: 18 Cze 2025, 00:58
-- Wersja serwera: 10.5.28-MariaDB-0+deb11u2
-- Wersja PHP: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Baza danych: `akoncew1`
--

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `tasks`
--

CREATE TABLE `tasks` (
  `id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `status` tinyint(1) DEFAULT 0,
  `completion_date` date DEFAULT NULL,
  `tags` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`tags`)),
  `assigned_user` int(11) DEFAULT NULL,
  `priority` tinyint(4) NOT NULL CHECK (`priority` between 1 and 4),
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Zrzut danych tabeli `tasks`
--

INSERT INTO `tasks` (`id`, `team_id`, `title`, `status`, `completion_date`, `tags`, `assigned_user`, `priority`, `created_at`) VALUES
(1, 1, 'Zaprojektować interfejs', 1, '2025-06-12', '[\"design\", \"frontend\"]', 1, 2, '2025-06-15 18:47:54'),
(3, 1, 'a', 1, '2025-06-15', '[\"a\"]', 1, 1, '2025-06-15 18:47:54'),
(12, 1, 'aaaaaaaaaa', 0, '2025-06-25', '[\"\\u0105\"]', 2, 1, '2025-06-15 18:47:54'),
(13, 1, 'sssss', 0, '2025-06-18', '[\"ss\"]', 2, 1, '2025-06-15 18:48:35'),
(14, 1, 'aaa', 0, NULL, '[\"a\"]', 2, 1, '2025-06-15 18:49:27'),
(17, 1, 'pogchamp', 0, '2025-06-15', '[\"pog\"]', 1, 1, '2025-06-15 18:56:33'),
(18, 1, 'meow', 0, '2025-06-15', '[\"meow\"]', 1, 1, '2025-06-15 19:18:17');

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `team`
--

CREATE TABLE `team` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `owner` int(11) DEFAULT NULL,
  `invite_code` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Zrzut danych tabeli `team`
--

INSERT INTO `team` (`id`, `name`, `owner`, `invite_code`) VALUES
(1, 'XDDDDD', 1, 'meow111'),
(2, 'Team_P4BVIU', 3, 'andrzej');

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `login` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `team_fk` int(11) DEFAULT NULL,
  `notification_settings` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`notification_settings`)),
  `nick` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Zrzut danych tabeli `users`
--

INSERT INTO `users` (`id`, `login`, `email`, `password_hash`, `team_fk`, `notification_settings`, `nick`) VALUES
(1, 'jan.kowalski', 'jan.kowalski@dziura.pl', '404cdd7bc109c432f8cc2443b45bcfe95980f5107215c645236e577929ac3e52', 1, '{\"new_task\": false, \"task_completed\": false, \"upcoming_deadline\": true, \"deadline_missed\": true}', 'Janek'),
(2, 'meow', 'meow@meow.com', '404cdd7bc109c432f8cc2443b45bcfe95980f5107215c645236e577929ac3e52', 1, '{\"new_task\": true, \"task_completed\": true, \"upcoming_deadline\": true, \"deadline_missed\": true}', 'Maciek'),
(3, 'Andrzej', 'andrzej@dzej.pl', '404cdd7bc109c432f8cc2443b45bcfe95980f5107215c645236e577929ac3e52', 2, NULL, 'Andrzej');

--
-- Indeksy dla zrzutów tabel
--

--
-- Indeksy dla tabeli `tasks`
--
ALTER TABLE `tasks`
  ADD PRIMARY KEY (`id`),
  ADD KEY `team_id` (`team_id`),
  ADD KEY `assigned_user` (`assigned_user`);

--
-- Indeksy dla tabeli `team`
--
ALTER TABLE `team`
  ADD PRIMARY KEY (`id`),
  ADD KEY `owner` (`owner`);

--
-- Indeksy dla tabeli `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `login` (`login`),
  ADD KEY `team_fk` (`team_fk`);

--
-- AUTO_INCREMENT dla zrzuconych tabel
--

--
-- AUTO_INCREMENT dla tabeli `tasks`
--
ALTER TABLE `tasks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT dla tabeli `team`
--
ALTER TABLE `team`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT dla tabeli `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Ograniczenia dla zrzutów tabel
--

--
-- Ograniczenia dla tabeli `tasks`
--
ALTER TABLE `tasks`
  ADD CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `team` (`id`),
  ADD CONSTRAINT `tasks_ibfk_2` FOREIGN KEY (`assigned_user`) REFERENCES `users` (`id`);

--
-- Ograniczenia dla tabeli `team`
--
ALTER TABLE `team`
  ADD CONSTRAINT `team_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `users` (`id`);

--
-- Ograniczenia dla tabeli `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`team_fk`) REFERENCES `team` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
