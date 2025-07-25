from universalagent.agents.entrypoint import create_worker_options
from livekit import agents

from dotenv import load_dotenv
_ = load_dotenv()

if __name__ == "__main__":
    worker_options = create_worker_options()
    agents.cli.run_app(worker_options) 
