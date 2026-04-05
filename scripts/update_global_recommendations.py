from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.services.recommendations import build_global_recommendations_snapshot
from app.storage.event_log import read_all_events
from app.storage.global_recommendations import write_global_recommendations


def main() -> int:
    events = read_all_events()
    snapshot = build_global_recommendations_snapshot(events)
    write_global_recommendations(snapshot)
    print(
        "Updated global recommendations snapshot: "
        f"events={snapshot.event_count}, users={snapshot.user_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
