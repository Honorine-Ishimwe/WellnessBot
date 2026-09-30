"""
WellnessBot — Application entry point.
Creates the Flask app using the factory and runs it.
"""

import os
from backend import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
