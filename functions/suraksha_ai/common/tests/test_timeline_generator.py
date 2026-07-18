from investigation.timeline_generator import TimelineGenerator
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestTimelineGenerator:
    def test_generate_returns_three_events(self):
        tl = TimelineGenerator()
        events = tl.generate(101)
        assert len(events) == 3

    def test_events_in_chronological_order(self):
        tl = TimelineGenerator()
        events = tl.generate(101)
        dates = [e.event_date for e in events]
        assert dates == sorted(dates)

    def test_event_types_present(self):
        tl = TimelineGenerator()
        events = tl.generate(101)
        types = {e.event_type for e in events}
        assert types == {"crime_registration", "arrest", "chargesheet"}

    def test_empty_case_id_still_returns_events(self):
        tl = TimelineGenerator()
        events = tl.generate(0)
        assert len(events) == 3
        assert events[0].event_type == "crime_registration"
