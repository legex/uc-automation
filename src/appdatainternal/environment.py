import os
import json

def get_env_config():
    env = os.environ.get("CONTAINER_APP_NAME", "localhost")
    is_staging = False

    if env != "localhost":
        try:
            with open("/a/etc/app_info", "r") as f:
                app_info_json = json.load(f)
                is_staging = app_info_json.get("is_staging", False)
                if is_staging is True:
                    env = env + "-stag"
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load app_info: {e}")

    app_env = "LOCAL"
    if env == "unifyx":
        app_env = "PROD"
    elif env == "unifyx-stag":
        app_env = "STAG"
    else:
        app_env = "LOCAL"
    return app_env
