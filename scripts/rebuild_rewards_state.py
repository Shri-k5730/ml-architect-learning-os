from __future__ import annotations

import json

from src.utils.cloud_state import repair_cloud_state_on_startup


if __name__ == "__main__":
    summary = repair_cloud_state_on_startup(force=True)
    print(json.dumps(summary, indent=2, default=str))
