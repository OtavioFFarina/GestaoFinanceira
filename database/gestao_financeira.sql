-- phpMyAdmin SQL Dump
-- version 5.2.1deb3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Tempo de geração: 01/03/2026 às 06:59
-- Versão do servidor: 8.0.45-0ubuntu0.24.04.1
-- Versão do PHP: 8.3.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `gestao_financeira`
--
CREATE DATABASE IF NOT EXISTS `gestao_financeira` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `gestao_financeira`;

-- --------------------------------------------------------

--
-- Estrutura para tabela `categorias`
--

CREATE TABLE `categorias` (
  `id` smallint UNSIGNED NOT NULL,
  `usuario_id` char(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nome` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `icone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cor_hex` char(7) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tipo` enum('entrada','saida','transferencia') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'saida',
  `ativa` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Dicionário de categorias financeiras. NULL em usuario_id = categoria global.';

--
-- Despejando dados para a tabela `categorias`
--

INSERT INTO `categorias` (`id`, `usuario_id`, `nome`, `slug`, `icone`, `cor_hex`, `tipo`, `ativa`, `created_at`, `updated_at`) VALUES
(1, NULL, 'Gastos Fixos', 'gastos_fixos', 'ShieldAlert', '#F85149', 'saida', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(2, NULL, 'Lazer', 'lazer', 'Palmtree', '#D2A12A', 'saida', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(3, NULL, 'Investimentos', 'investimentos', 'TrendingUp', '#4BADE8', 'saida', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(4, NULL, 'Estudos', 'estudos', 'GraduationCap', '#B266C9', 'saida', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(5, NULL, 'Reserva', 'reserva', 'Wallet', '#5CA34F', 'saida', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(6, NULL, 'Salário', 'salario', 'Banknote', '#7CC96E', 'entrada', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(7, NULL, 'Renda Extra', 'renda_extra', 'Coins', '#7CC96E', 'entrada', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16'),
(8, NULL, 'Outros', 'outros', 'MoreHorizontal', '#8B949E', 'saida', 1, '2026-03-01 02:45:16', '2026-03-01 02:45:16');

-- --------------------------------------------------------

--
-- Estrutura para tabela `ciclos_mensais`
--

CREATE TABLE `ciclos_mensais` (
  `id` bigint UNSIGNED NOT NULL,
  `usuario_id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ano` smallint NOT NULL,
  `mes` tinyint UNSIGNED NOT NULL,
  `renda_total` decimal(12,2) NOT NULL DEFAULT '0.00',
  `observacoes` text COLLATE utf8mb4_unicode_ci,
  `fechado` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `metas`
--

CREATE TABLE `metas` (
  `id` bigint UNSIGNED NOT NULL,
  `usuario_id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `titulo` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descricao` text COLLATE utf8mb4_unicode_ci,
  `valor_alvo` decimal(12,2) NOT NULL,
  `valor_atual` decimal(12,2) NOT NULL DEFAULT '0.00',
  `prazo` date NOT NULL,
  `categoria_id` smallint UNSIGNED DEFAULT NULL,
  `status` enum('ativa','concluida','cancelada') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ativa',
  `ia_dicas` text COLLATE utf8mb4_unicode_ci COMMENT 'JSON array com dicas geradas pela IA',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `metas_alocacao`
--

CREATE TABLE `metas_alocacao` (
  `id` bigint UNSIGNED NOT NULL,
  `ciclo_id` bigint UNSIGNED NOT NULL,
  `categoria_id` smallint UNSIGNED NOT NULL,
  `valor_planejado` decimal(12,2) NOT NULL DEFAULT '0.00',
  `percentual` decimal(5,2) DEFAULT NULL COMMENT 'Percentual da renda total do ciclo. Calculado na aplicação.',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `perfil_usuario`
--

CREATE TABLE `perfil_usuario` (
  `usuario_id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome_exibicao` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Usuário',
  `foto_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tema` enum('dark','light') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'dark',
  `meses_historico` tinyint NOT NULL DEFAULT '12' COMMENT 'Quantos meses de histórico o usuário quer reter',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Preferências e dados de exibição do usuário.';

--
-- Despejando dados para a tabela `perfil_usuario`
--

INSERT INTO `perfil_usuario` (`usuario_id`, `nome_exibicao`, `foto_url`, `tema`, `meses_historico`, `updated_at`) VALUES
('00000000-0000-0000-0000-000000000001', 'Demo', NULL, 'dark', 12, '2026-03-01 03:59:12');

-- --------------------------------------------------------

--
-- Estrutura para tabela `sessoes`
--

CREATE TABLE `sessoes` (
  `id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (uuid()),
  `usuario_id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` char(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expires_at` datetime NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Sessões de autenticação por token.';

-- --------------------------------------------------------

--
-- Estrutura para tabela `transacoes`
--

CREATE TABLE `transacoes` (
  `id` bigint UNSIGNED NOT NULL,
  `ciclo_id` bigint UNSIGNED NOT NULL,
  `categoria_id` smallint UNSIGNED NOT NULL,
  `descricao` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor` decimal(12,2) NOT NULL,
  `tipo` enum('entrada','saida') COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_transacao` date NOT NULL,
  `recorrente` tinyint(1) NOT NULL DEFAULT '0',
  `observacoes` text COLLATE utf8mb4_unicode_ci,
  `fonte_ia` tinyint(1) NOT NULL DEFAULT '0' COMMENT '1 se a transação foi sugerida/importada pelo Agente de IA',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `users`
--

CREATE TABLE `users` (
  `id` char(36) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (uuid()),
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `senha_hash` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ativo` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Usuários do sistema. Preparado para multi-tenant.';

--
-- Despejando dados para a tabela `users`
--

INSERT INTO `users` (`id`, `nome`, `email`, `senha_hash`, `ativo`, `created_at`, `updated_at`) VALUES
('00000000-0000-0000-0000-000000000001', 'Usuário Demo', 'demo@gestaofinanceira.app', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGkRtpHO9Fc.SQjKIWaHbMJm7JC', 1, '2026-03-01 03:59:12', '2026-03-01 03:59:12');

-- --------------------------------------------------------

--
-- Estrutura stand-in para view `vw_planejado_vs_realizado`
-- (Veja abaixo para a visão atual)
--
CREATE TABLE `vw_planejado_vs_realizado` (
`ciclo_id` bigint unsigned
,`usuario_id` char(36)
,`ano` smallint
,`mes` tinyint unsigned
,`categoria_id` smallint unsigned
,`categoria` varchar(80)
,`slug` varchar(80)
,`cor_hex` char(7)
,`valor_planejado` decimal(12,2)
,`percentual_planejado` decimal(5,2)
,`valor_realizado` decimal(34,2)
,`percentual_realizado` decimal(40,2)
);

-- --------------------------------------------------------

--
-- Estrutura para view `vw_planejado_vs_realizado`
--
DROP TABLE IF EXISTS `vw_planejado_vs_realizado`;

CREATE ALGORITHM=UNDEFINED DEFINER=`admin`@`localhost` SQL SECURITY DEFINER VIEW `vw_planejado_vs_realizado`  AS SELECT `cm`.`id` AS `ciclo_id`, `cm`.`usuario_id` AS `usuario_id`, `cm`.`ano` AS `ano`, `cm`.`mes` AS `mes`, `c`.`id` AS `categoria_id`, `c`.`nome` AS `categoria`, `c`.`slug` AS `slug`, `c`.`cor_hex` AS `cor_hex`, coalesce(`ma`.`valor_planejado`,0.00) AS `valor_planejado`, coalesce(`ma`.`percentual`,0.00) AS `percentual_planejado`, coalesce(sum(`t`.`valor`),0.00) AS `valor_realizado`, round(((coalesce(sum(`t`.`valor`),0.00) / nullif(`cm`.`renda_total`,0)) * 100),2) AS `percentual_realizado` FROM (((`ciclos_mensais` `cm` join `categorias` `c`) left join `metas_alocacao` `ma` on(((`ma`.`ciclo_id` = `cm`.`id`) and (`ma`.`categoria_id` = `c`.`id`)))) left join `transacoes` `t` on(((`t`.`ciclo_id` = `cm`.`id`) and (`t`.`categoria_id` = `c`.`id`) and (`t`.`tipo` = 'saida')))) WHERE ((`c`.`ativa` = 1) AND (`c`.`tipo` = 'saida')) GROUP BY `cm`.`id`, `cm`.`usuario_id`, `cm`.`ano`, `cm`.`mes`, `c`.`id`, `c`.`nome`, `c`.`slug`, `c`.`cor_hex`, `ma`.`valor_planejado`, `ma`.`percentual`, `cm`.`renda_total` ;

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `categorias`
--
ALTER TABLE `categorias`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_categoria_slug_user` (`usuario_id`,`slug`),
  ADD KEY `idx_categorias_usuario` (`usuario_id`);

--
-- Índices de tabela `ciclos_mensais`
--
ALTER TABLE `ciclos_mensais`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_ciclo_usuario_mes` (`usuario_id`,`ano`,`mes`),
  ADD KEY `idx_ciclos_usuario_periodo` (`usuario_id`,`ano`,`mes`);

--
-- Índices de tabela `metas`
--
ALTER TABLE `metas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_meta_cat` (`categoria_id`),
  ADD KEY `idx_metas_usuario` (`usuario_id`,`status`);

--
-- Índices de tabela `metas_alocacao`
--
ALTER TABLE `metas_alocacao`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_meta_ciclo_categoria` (`ciclo_id`,`categoria_id`),
  ADD KEY `fk_meta_categoria` (`categoria_id`),
  ADD KEY `idx_metas_ciclo` (`ciclo_id`);

--
-- Índices de tabela `perfil_usuario`
--
ALTER TABLE `perfil_usuario`
  ADD PRIMARY KEY (`usuario_id`);

--
-- Índices de tabela `sessoes`
--
ALTER TABLE `sessoes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_sessao_token` (`token`),
  ADD KEY `idx_sessoes_token` (`token`),
  ADD KEY `idx_sessoes_usuario` (`usuario_id`);

--
-- Índices de tabela `transacoes`
--
ALTER TABLE `transacoes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_transacoes_ciclo` (`ciclo_id`),
  ADD KEY `idx_transacoes_categoria` (`categoria_id`),
  ADD KEY `idx_transacoes_data` (`data_transacao`),
  ADD KEY `idx_transacoes_ciclo_data` (`ciclo_id`,`data_transacao`);

--
-- Índices de tabela `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_users_email` (`email`),
  ADD KEY `idx_users_email` (`email`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `categorias`
--
ALTER TABLE `categorias`
  MODIFY `id` smallint UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de tabela `ciclos_mensais`
--
ALTER TABLE `ciclos_mensais`
  MODIFY `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `metas`
--
ALTER TABLE `metas`
  MODIFY `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `metas_alocacao`
--
ALTER TABLE `metas_alocacao`
  MODIFY `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `transacoes`
--
ALTER TABLE `transacoes`
  MODIFY `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `categorias`
--
ALTER TABLE `categorias`
  ADD CONSTRAINT `fk_cat_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Restrições para tabelas `ciclos_mensais`
--
ALTER TABLE `ciclos_mensais`
  ADD CONSTRAINT `fk_ciclo_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Restrições para tabelas `metas`
--
ALTER TABLE `metas`
  ADD CONSTRAINT `fk_meta_cat` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_meta_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Restrições para tabelas `metas_alocacao`
--
ALTER TABLE `metas_alocacao`
  ADD CONSTRAINT `fk_meta_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_meta_ciclo` FOREIGN KEY (`ciclo_id`) REFERENCES `ciclos_mensais` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Restrições para tabelas `perfil_usuario`
--
ALTER TABLE `perfil_usuario`
  ADD CONSTRAINT `fk_perfil_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Restrições para tabelas `sessoes`
--
ALTER TABLE `sessoes`
  ADD CONSTRAINT `fk_sessao_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

--
-- Restrições para tabelas `transacoes`
--
ALTER TABLE `transacoes`
  ADD CONSTRAINT `fk_transacao_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_transacao_ciclo` FOREIGN KEY (`ciclo_id`) REFERENCES `ciclos_mensais` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
