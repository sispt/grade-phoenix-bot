-- Drop the old grade_history table if it exists
DROP TABLE IF EXISTS grade_history CASCADE;

-- Add a new unique column to users for FK
ALTER TABLE users ADD COLUMN username_unique VARCHAR(100);
UPDATE users SET username_unique = username;
ALTER TABLE users ADD CONSTRAINT unique_username_unique UNIQUE (username_unique);

-- Drop the old grades table if it exists
DROP TABLE IF EXISTS grades CASCADE;

-- Create the new grades table with username_unique as FK
CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    username_unique VARCHAR(100) NOT NULL REFERENCES users(username_unique) ON DELETE CASCADE,
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
    CONSTRAINT unique_user_course UNIQUE (username_unique, code)
);

-- Indexes for performance
CREATE INDEX idx_grade_username_unique ON grades(username_unique);
CREATE INDEX idx_grade_code ON grades(code);
CREATE INDEX idx_grade_status ON grades(grade_status);
CREATE INDEX idx_grade_numeric ON grades(numeric_grade); 