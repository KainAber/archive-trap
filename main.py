from pathlib import Path

import yaml

from src.run import ArxivFilterRun

if __name__ == "__main__":
    # Create path to config
    project_root_folder_path = Path(__file__).resolve().parents[0]

    # Read config dictionary
    with open(project_root_folder_path / "setup_config.yml", "r") as file:
        setup_cfg_dict = yaml.safe_load(file)

    # Extract and read run config
    with open(project_root_folder_path / setup_cfg_dict["run config"], "r") as file:
        run_cfg_dict = yaml.safe_load(file)

    # Create run object
    run = ArxivFilterRun(run_cfg_dict)

    # Execute run
    run.execute()
