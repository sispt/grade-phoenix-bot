-- Drop the old grade_history table if it exists
DROP TABLE IF EXISTS grade_history CASCADE;

-- Drop the old grades table if it exists
DROP TABLE IF EXISTS grades CASCADE;

-- Create the new grades table with unified terminology
CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    ects NUMERIC(3, 1),
    coursework VARCHAR(20),
    final_exam VARCHAR(20),
    total VARCHAR(20),
    numeric_grade NUMERIC(5, 2),
    grade_status VARCHAR(20) NOT NULL DEFAULT 'Not Published',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_course UNIQUE (telegram_id, code)
);

-- Indexes for performance
CREATE INDEX idx_grade_telegram_id ON grades(telegram_id);
CREATE INDEX idx_grade_code ON grades(code);
CREATE INDEX idx_grade_status ON grades(grade_status);
CREATE INDEX idx_grade_numeric ON grades(numeric_grade); 