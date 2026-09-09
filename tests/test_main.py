import asyncio
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.api.health import health_check
from src.app.api.dashboard import get_dashboard_stats
from src.app.models.schema import (
    Base,
    BronzeMoodleLogEvent,
    MoodleParticipantEmailExclusion,
    RawMoodleParticipant,
    Registration,
)
from src.app.services.member_service import parse_member_list_from_csv
from src.app.services.moodle_log_service import import_moodle_log_csv, parse_moodle_log_row
from src.app.services.moodle_participant_service import (
    import_moodle_participants_csv,
    parse_moodle_participant_row,
)
from src.app.utils.text_utils import normalized_team_name


class TestBasicSetup(unittest.TestCase):
    def test_environment_ready(self):
        self.assertTrue(True, "Test environment is ready.")

    def test_health_endpoint_returns_ok(self):
        response = asyncio.run(health_check())

        self.assertEqual(response["status"], "ok")

    def test_registration_long_text_columns_cover_form_answers(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")

        self.assertIn('"team_name"', database_py)
        self.assertIn('"project_domain"', database_py)
        self.assertIn('"source"', database_py)

    def test_silver_learning_view_is_created_on_startup(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")
        main_py = Path("src/app/main.py").read_text(encoding="utf-8")

        self.assertIn("def ensure_moodle_silver_learning_events_view", database_py)
        self.assertIn("CREATE OR REPLACE VIEW silver_moodle_learning_events", database_py)
        self.assertIn("ensure_moodle_silver_learning_events_view()", main_py)

    def test_silver_summary_endpoint_is_available(self):
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn('@router.get("/silver-summary")', api_py)
        self.assertIn("FROM silver_moodle_learning_events", api_py)

    def test_activity_dimension_view_is_created_on_startup(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")
        main_py = Path("src/app/main.py").read_text(encoding="utf-8")
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn("def ensure_moodle_course_activities_view", database_py)
        self.assertIn("CREATE OR REPLACE VIEW dim_moodle_course_activities", database_py)
        self.assertIn("ensure_moodle_course_activities_view()", main_py)
        self.assertIn('@router.get("/activity-dim-summary")', api_py)

    def test_gold_user_summary_view_is_created_on_startup(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")
        main_py = Path("src/app/main.py").read_text(encoding="utf-8")
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn("def ensure_gold_user_learning_summary_view", database_py)
        self.assertIn("CREATE OR REPLACE VIEW gold_user_learning_summary", database_py)
        self.assertIn("ensure_gold_user_learning_summary_view()", main_py)
        self.assertIn('@router.get("/gold-user-summary")', api_py)

    def test_gold_registered_user_summary_view_is_created_on_startup(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")
        main_py = Path("src/app/main.py").read_text(encoding="utf-8")
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn("def ensure_gold_registered_user_learning_summary_view", database_py)
        self.assertIn("CREATE OR REPLACE VIEW gold_registered_user_learning_summary", database_py)
        self.assertIn("ensure_gold_registered_user_learning_summary_view()", main_py)
        self.assertIn('@router.get("/gold-registered-user-summary")', api_py)

    def test_gold_team_summary_view_is_created_on_startup(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")
        main_py = Path("src/app/main.py").read_text(encoding="utf-8")
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn("def ensure_gold_team_learning_summary_view", database_py)
        self.assertIn("CREATE OR REPLACE VIEW gold_team_learning_summary", database_py)
        self.assertIn("ensure_gold_team_learning_summary_view()", main_py)
        self.assertIn('@router.get("/gold-team-summary")', api_py)

    def test_gold_individual_summary_view_is_created_on_startup(self):
        database_py = Path("src/app/core/database.py").read_text(encoding="utf-8")
        main_py = Path("src/app/main.py").read_text(encoding="utf-8")
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn("def ensure_gold_individual_learning_summary_view", database_py)
        self.assertIn("CREATE OR REPLACE VIEW gold_individual_learning_summary", database_py)
        self.assertIn("ensure_gold_individual_learning_summary_view()", main_py)
        self.assertIn('@router.get("/gold-individual-summary")', api_py)

    def test_learning_dashboard_overview_endpoint_is_available(self):
        api_py = Path("src/app/api/moodle_logs.py").read_text(encoding="utf-8")

        self.assertIn('@router.get("/learning-dashboard-overview")', api_py)
        self.assertIn("FROM gold_registered_user_learning_summary", api_py)
        self.assertIn("FROM gold_team_learning_summary", api_py)
        self.assertIn("FROM gold_individual_learning_summary", api_py)
        self.assertIn("FROM dim_moodle_course_activities", api_py)
        self.assertIn('@router.get("/team-activities-detail")', api_py)
        self.assertIn('@router.get("/individual-activities-detail")', api_py)
        self.assertIn("empty_activity_note", api_py)

    def test_learning_dashboard_frontend_is_available(self):
        index_html = Path("src/app/static/index.html").read_text(encoding="utf-8")
        learning_js = Path("src/app/static/learning-dashboard.js").read_text(encoding="utf-8")

        self.assertIn('data-target="learningDashboardView"', index_html)
        self.assertIn('id="learningDashboardView"', index_html)
        self.assertIn('learning-dashboard.js?v=7', index_html)
        self.assertIn('/api/v1/moodle-logs/learning-dashboard-overview', learning_js)
        self.assertIn('/api/v1/moodle-logs/gold-team-summary', learning_js)
        self.assertIn('/api/v1/moodle-logs/team-activities-detail', learning_js)
        self.assertIn('/api/v1/moodle-logs/individual-activities-detail', learning_js)
        self.assertIn('/api/v1/moodle-logs/gold-individual-summary', learning_js)
        self.assertIn('data-team-key', learning_js)
        self.assertIn('data-individual-email', learning_js)
        self.assertIn('renderModalTeamActivities', learning_js)
        self.assertIn('renderModalIndividualActivities', learning_js)
        self.assertIn('renderActivityMetricChips', learning_js)

    def test_msforms_parser_uses_header_based_columns(self):
        service_py = Path("src/app/services/msforms_service.py").read_text(encoding="utf-8")

        self.assertIn("build_header_index(ws)", service_py)
        self.assertIn('find_header_index(header_indices, "danh sach thanh vien"', service_py)
        self.assertIn("looks_like_sheet_url(sheet_link)", service_py)

    def test_member_parser_supports_full_name_template(self):
        csv_content = "\n".join([
            "Danh sach thanh vien/Member List,,,,,,,,,,,,",
            "Ten du an,,DIEP THANH BANG,,,,,,,,,,",
            "#,Ho va ten/ Full name,Email,So dien thoai/ Phone number,Ngay sinh,DOB,Tinh,Ten truong,Role,MSSV,Khoa - Lop,Nganh hoc,Ghi chu",
            ",,,,,,,,,MSSV,Khoa - Lop,Nganh hoc,Ghi chu",
            "1,Thach Thi Bich Tram,tram@example.com,0393957493,24/9/2009,Nu,,THPT Long Hiep,Truong nhom,x,x,x,",
        ])

        team_name, members, errors = parse_member_list_from_csv(csv_content)

        self.assertEqual(team_name, "DIEP THANH BANG")
        self.assertEqual(errors, [])
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].first_name, "Tram")
        self.assertEqual(members[0].last_name, "Thach Thi Bich")
        self.assertEqual(members[0].email, "tram@example.com")
        self.assertIsNone(members[0].student_id)

    def test_member_parser_supports_gviz_collapsed_template(self):
        csv_content = "\n".join([
            "Danh sach thanh vien/Member List Ten du an #,Ho va ten/ Full name,Fishomic Email,So dien thoai/ Phone number,Ngay sinh,Gioi tinh,Dia chi thuong tru,Ten truong,Role,MSSV,Khoa - Lop,Nganh hoc,Ghi chu",
            "1,Ly Thi Hong Nhung,nhung@example.com,0378920138,26/02/2005,Nu,,UEH,Truong nhom,31241022143,K50,Quan tri,",
            "2,Ha Ngoc Minh Anh,anh@example.com,0948910618,29/07/2006,Nu,,UEH,Thanh vien,31241024624,K50,Quan tri,",
        ])

        team_name, members, errors = parse_member_list_from_csv(csv_content)

        self.assertEqual(team_name, "Fishomic")
        self.assertEqual(errors, [])
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0].full_name, "Ly Thi Hong Nhung")
        self.assertEqual(members[1].email, "anh@example.com")

    def test_moodle_log_parser_extracts_core_ids(self):
        row = {
            "Time": "7/09/26, 21:40:58",
            "User full name": "Chau Bui Tran Minh",
            "Affected user": "-",
            "Event context": "Page: FAQ",
            "Component": "Page",
            "Event name": "Course module viewed",
            "Description": "The user with id '1046' viewed the 'page' activity with course module id '643'.",
            "Origin": "web",
            "IP address": "172.18.0.1",
        }

        event = parse_moodle_log_row(row, raw_file_id=1)

        self.assertEqual(event.moodle_user_id, 1046)
        self.assertEqual(event.moodle_course_module_id, 643)
        self.assertEqual(event.context_type, "Page")
        self.assertEqual(event.context_name, "FAQ")
        self.assertEqual(event.event_category, "learning")
        self.assertTrue(event.is_learning_event)

    def test_moodle_log_parser_extracts_xapi_ids_with_the_id_phrase(self):
        row = {
            "Time": "7/09/26, 21:40:58",
            "User full name": "Loc Nguyen Ba",
            "Affected user": "-",
            "Event context": "H5P: MILESTONE GUIDELINE: Market Segmentation",
            "Component": "H5P",
            "Event name": "xAPI statement received",
            "Description": "The user with the id '982' send a tracking statement for a H5P activity with the course module id '650'.",
            "Origin": "web",
            "IP address": "172.18.0.1",
        }

        event = parse_moodle_log_row(row, raw_file_id=1)

        self.assertEqual(event.moodle_user_id, 982)
        self.assertEqual(event.moodle_course_module_id, 650)
        self.assertEqual(event.context_type, "H5P")
        self.assertEqual(event.event_category, "learning")
        self.assertTrue(event.is_learning_event)

    def test_moodle_log_parser_marks_submission_events_as_learning(self):
        row = {
            "Time": "9/09/26, 16:35:30",
            "User full name": "Loc Nguyen Ba",
            "Affected user": "-",
            "Event context": "Assignment: MILESTONE 4 SUBMISSION",
            "Component": "Assignment",
            "Event name": "A submission has been submitted.",
            "Description": "The user with id '982' has submitted the submission with id '1961' for the assignment with course module id '660'.",
            "Origin": "web",
            "IP address": "172.18.0.1",
        }

        event = parse_moodle_log_row(row, raw_file_id=1)

        self.assertEqual(event.moodle_user_id, 982)
        self.assertEqual(event.moodle_course_module_id, 660)
        self.assertEqual(event.context_type, "Assignment")
        self.assertEqual(event.context_name, "MILESTONE 4 SUBMISSION")
        self.assertEqual(event.event_category, "learning")
        self.assertTrue(event.is_learning_event)

    def test_moodle_log_import_is_idempotent(self):
        engine = create_engine("sqlite:///:memory:")
        TestingSession = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = TestingSession()
        csv_content = "\n".join([
            'Time,"User full name","Affected user","Event context",Component,"Event name",Description,Origin,"IP address"',
            '"7/09/26, 21:40:58","Chau Bui Tran Minh",-,"Page: FAQ",Page,"Course module viewed","The user with id \'1046\' viewed the \'page\' activity with course module id \'643\'.",web,172.18.0.1',
            '"7/09/26, 21:40:58","Chau Bui Tran Minh",-,"Page: FAQ",Page,"Course module viewed","The user with id \'1046\' viewed the \'page\' activity with course module id \'643\'.",web,172.18.0.1',
        ]).encode("utf-8")

        first_report = import_moodle_log_csv(db, csv_content, "sample.csv")
        second_report = import_moodle_log_csv(db, csv_content, "sample.csv")

        event_count = db.query(BronzeMoodleLogEvent).count()
        self.assertEqual(first_report["inserted_count"], 2)
        self.assertEqual(second_report["inserted_count"], 0)
        self.assertEqual(second_report["duplicate_count"], 2)
        self.assertEqual(event_count, 2)
        db.close()

    def test_moodle_log_import_deduplicates_overlapping_exports(self):
        engine = create_engine("sqlite:///:memory:")
        TestingSession = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = TestingSession()
        csv_content = "\n".join([
            'Time,"User full name","Affected user","Event context",Component,"Event name",Description,Origin,"IP address"',
            '"7/09/26, 21:40:58","Chau Bui Tran Minh",-,"Page: FAQ",Page,"Course module viewed","The user with id \'1046\' viewed the \'page\' activity with course module id \'643\'.",web,172.18.0.1',
            '"7/09/26, 21:40:58","Chau Bui Tran Minh",-,"Page: FAQ",Page,"Course module viewed","The user with id \'1046\' viewed the \'page\' activity with course module id \'643\'.",web,172.18.0.1',
        ]).encode("utf-8")

        first_report = import_moodle_log_csv(db, csv_content, "first_export.csv")
        second_report = import_moodle_log_csv(db, csv_content, "latest_export.csv")

        event_count = db.query(BronzeMoodleLogEvent).count()
        self.assertEqual(first_report["inserted_count"], 2)
        self.assertEqual(second_report["inserted_count"], 0)
        self.assertEqual(second_report["duplicate_count"], 2)
        self.assertEqual(event_count, 2)
        db.close()

    def test_moodle_participant_parser_builds_identity_keys(self):
        row = {
            "First name": "Châu",
            "Last name": "Bùi Trần Minh",
            "Email address": " Chaubui.31241022356@st.ueh.edu.vn ",
            "Groups": "Fishomic",
        }

        participant = parse_moodle_participant_row(row, raw_file_id=1, course_id=12)

        self.assertEqual(participant.moodle_full_name, "Châu Bùi Trần Minh")
        self.assertEqual(participant.moodle_full_name_key, "châu bùi trần minh")
        self.assertEqual(participant.email, "chaubui.31241022356@st.ueh.edu.vn")
        self.assertEqual(participant.moodle_group_name, "Fishomic")
        self.assertEqual(participant.course_id, 12)

    def test_moodle_participant_import_is_idempotent(self):
        engine = create_engine("sqlite:///:memory:")
        TestingSession = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = TestingSession()
        csv_content = "\n".join([
            '"First name","Last name","Email address","Groups"',
            '"Châu","Bùi Trần Minh","chaubui.31241022356@st.ueh.edu.vn","Fishomic"',
            '"Châu","Bùi Trần Minh","chaubui.31241022356@st.ueh.edu.vn","Fishomic"',
        ]).encode("utf-8")

        first_report = import_moodle_participants_csv(db, csv_content, "participants.csv", course_id=12)
        second_report = import_moodle_participants_csv(db, csv_content, "participants.csv", course_id=12)

        participant_count = db.query(RawMoodleParticipant).count()
        self.assertEqual(first_report["inserted_count"], 2)
        self.assertEqual(second_report["inserted_count"], 0)
        self.assertEqual(second_report["duplicate_count"], 2)
        self.assertEqual(participant_count, 2)
        db.close()

    def test_moodle_participant_import_skips_excluded_email(self):
        engine = create_engine("sqlite:///:memory:")
        TestingSession = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = TestingSession()
        db.add(MoodleParticipantEmailExclusion(email="sai@example.com", reason="Email test"))
        db.commit()
        csv_content = "\n".join([
            '"First name","Last name","Email address","Groups"',
            '"Dung","Nguyen Van","dung@example.com","Team A"',
            '"Sai","Email","sai@example.com","Team B"',
        ]).encode("utf-8")

        report = import_moodle_participants_csv(db, csv_content, "participants.csv", course_id=12)

        participant_count = db.query(RawMoodleParticipant).count()
        self.assertEqual(report["inserted_count"], 1)
        self.assertEqual(report["excluded_count"], 1)
        self.assertEqual(participant_count, 1)
        db.close()

    def test_team_name_normalization_uses_canonical_aliases(self):
        self.assertEqual(
            normalized_team_name("Stabily - Thiết bị đeo ổn định chuyển động tay cho người mắc Parkinson"),
            "STABILY - Thiết bị đeo ổn định chuyển động tay cho người mắc Parkinson",
        )
        self.assertEqual(normalized_team_name("  Weave   Carbon  "), "Weave Carbon")

    def test_dashboard_counts_teams_by_normalized_key(self):
        engine = create_engine("sqlite:///:memory:")
        TestingSession = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = TestingSession()
        db.add_all([
            Registration(full_name="A", email="a@example.com", role="Leader", team_name="Team Alpha"),
            Registration(full_name="B", email="b@example.com", role="Member", team_name=" team alpha "),
            Registration(full_name="C", email="c@example.com", role="Individual", team_name=None),
            Registration(full_name="D", email="d@example.com", role="Individual", team_name=""),
        ])
        db.commit()

        response = get_dashboard_stats(db)

        self.assertEqual(response["summary"]["total_users"], 4)
        self.assertEqual(response["summary"]["total_teams"], 1)
        self.assertEqual(response["summary"]["total_individuals"], 2)
        db.close()


if __name__ == "__main__":
    unittest.main()
