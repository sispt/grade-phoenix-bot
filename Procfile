# Run migration if DATABASE_MIGRATE is true, then always start the bot
web: bash -c 'if [ "$DATABASE_MIGRATE" = "true" ]; then python migration.py && sleep 3; fi; python main.py'