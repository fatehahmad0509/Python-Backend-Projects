# Entry point for the RepairHub application.
# Initializes the database and launches the GUI.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from utils.logger import logger

if __name__ == "__main__":
    logger.info("Starting RepairHub...")
    init_db()
    logger.info("Database is ready.")
    from frontend.app import main
    main()
