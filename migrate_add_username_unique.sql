-- Add username_unique column to users if it does not exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS username_unique VARCHAR(100);

-- Populate username_unique with username for all existing users
UPDATE users SET username_unique = username WHERE username_unique IS NULL OR username_unique = '';

-- Add a unique constraint on username_unique if not already present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name='users' AND constraint_type='UNIQUE' AND constraint_name='unique_username_unique'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT unique_username_unique UNIQUE (username_unique);
    END IF;
END$$; 