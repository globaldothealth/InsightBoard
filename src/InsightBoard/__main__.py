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
        logging.basicConfig(level=logging.DEBUG)
        app.run(debug=True)
    else:
        # Otherwise, launch the production server
        main()
