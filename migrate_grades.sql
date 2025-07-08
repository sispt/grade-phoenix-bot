-- Drop the old grades table if it exists
DROP TABLE IF EXISTS grades CASCADE;

-- Create the new grades table
CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    course_name VARCHAR(255) NOT NULL,
    course_code VARCHAR(50),
    ects_credits NUMERIC(3, 1),
    coursework_grade VARCHAR(20),
    final_exam_grade VARCHAR(20),
    total_grade_value VARCHAR(20),
    numeric_grade NUMERIC(5, 2),
    grade_status VARCHAR(20) NOT NULL DEFAULT 'Not Published',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_course UNIQUE (telegram_id, course_code)
);

-- Indexes for performance
CREATE INDEX idx_grade_telegram_id ON grades(telegram_id);
CREATE INDEX idx_grade_course_code ON grades(course_code);
CREATE INDEX idx_grade_status ON grades(grade_status);
CREATE INDEX idx_grade_numeric ON grades(numeric_grade); 