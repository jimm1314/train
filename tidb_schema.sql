-- ============================================
-- 面试题刷题系统 - 完整数据库表结构
-- 兼容 TiDB/MySQL 和 SQLite
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    is_admin TINYINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 题库表
CREATE TABLE IF NOT EXISTS interview_questions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question TEXT NOT NULL,
    answer TEXT,
    is_visible TINYINT DEFAULT 1,
    source VARCHAR(50) NOT NULL DEFAULT '',
    category VARCHAR(50) NOT NULL DEFAULT '未分类',
    difficulty VARCHAR(20) NOT NULL DEFAULT '中等',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_category (category),
    INDEX idx_is_visible (is_visible),
    FULLTEXT INDEX ft_question (question),
    FULLTEXT INDEX ft_answer (answer)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 默写草稿表
CREATE TABLE IF NOT EXISTS dictation_drafts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    date_str VARCHAR(20) NOT NULL,
    question TEXT NOT NULL,
    reference_answer TEXT,
    my_answer TEXT,
    draft_key VARCHAR(200) NOT NULL,
    updated_at VARCHAR(20),
    UNIQUE KEY uk_user_key (username, draft_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 错题本表
CREATE TABLE IF NOT EXISTS review_book (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    date_str VARCHAR(20) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    note TEXT,
    mastery INT DEFAULT 0,
    review_count INT DEFAULT 0,
    tags VARCHAR(200) DEFAULT '',
    attribution VARCHAR(50) DEFAULT '',
    next_review VARCHAR(20) NOT NULL,
    ease_factor FLOAT DEFAULT 2.5,
    review_interval INT DEFAULT 1,
    repetitions INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_next_review (username, next_review)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 学习日志表
CREATE TABLE IF NOT EXISTS study_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    date_str VARCHAR(20) NOT NULL,
    count INT NOT NULL DEFAULT 0,
    activity_type VARCHAR(20) NOT NULL DEFAULT '抽题',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username_date (username, date_str)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户历史回答表
CREATE TABLE IF NOT EXISTS user_answers (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    reference_answer TEXT,
    user_answer TEXT NOT NULL,
    score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username_question (username, question(100)),
    INDEX idx_username_created (username, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 签到记录表
CREATE TABLE IF NOT EXISTS checkin_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    date_str VARCHAR(20) NOT NULL,
    checkin_time VARCHAR(20) NOT NULL,
    activity_type VARCHAR(20) NOT NULL DEFAULT '学习',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_user_date_type (username, date_str, activity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 默写记录表
CREATE TABLE IF NOT EXISTS dictation_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    date_str VARCHAR(20) NOT NULL,
    question TEXT NOT NULL,
    reference_answer TEXT,
    my_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username_date (username, date_str)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户学习目标表
CREATE TABLE IF NOT EXISTS user_goals (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    daily_questions INT DEFAULT 20,
    weekly_questions INT DEFAULT 100,
    daily_review INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
