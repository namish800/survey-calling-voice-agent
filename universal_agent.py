from src.agents.entrypoint import create_worker_options
from livekit import agents

if __name__ == "__main__":
    worker_options = create_worker_options()
    agents.cli.run_app(worker_options) 
