import logging
import argparse
from InsightBoard import main
from InsightBoard.app import app


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    if args.debug:
        # Dash launches a Flask development server
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
        logging.basicConfig(level=logging.INFO)
        app.run(debug=True)
    else:
        # Otherwise, launch the production server
        main()
