from base64 import b64decode
import json
from pathlib import Path
import unittest

import numpy as np
from streamlit.testing.v1 import AppTest

from gold import load_marts


ENTRY_POINT = Path(__file__).with_name("dashboard.py")
GEMMA = "google/gemma-4-e2b"
MINISTRAL = "mistralai/ministral-3-3b"
P1 = "P1_choices"
P3 = "P3_expert_advanced"


def chart(app, key):
    element, = [item for item in app.get("plotly_chart") if item.proto.id.endswith(f"-{key}")]
    return json.loads(element.proto.spec)


def trace_values(trace, key):
    values = trace[key]
    if isinstance(values, dict):
        return np.frombuffer(b64decode(values["bdata"]), dtype=values["dtype"]).tolist()
    return values


def bar_value(figure, series, label):
    trace, = [item for item in figure["data"] if item["name"] == series]
    return dict(zip(trace_values(trace, "x"), trace_values(trace, "y"), strict=True))[label]


def active_filter(widgets, key):
    widget, = [item for item in widgets if item.key == key or item.key.startswith(f"{key}__")]
    return widget


class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(ENTRY_POINT, default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def test_marts_and_global_performance(self):
        expected = {
            "mart_performance": (6, 11), "mart_prompt_comparison": (6, 17),
            "mart_category": (144, 7), "mart_category_gap": (72, 7),
            "mart_difficulty": (54, 9), "mart_question_type": (12, 9),
            "mart_question_outcomes": (5290, 14),
        }
        self.assertEqual({name: frame.shape for name, frame in load_marts().items()}, expected)
        for key, gemma, ministral, digits in (
            ("global_accuracy", 54.12, 41.25, 2),
            ("global_compliance", 100, 78.75, 2),
            ("global_latency", 0.463, 1.092, 3),
        ):
            figure = chart(self.app, key)
            self.assertAlmostEqual(bar_value(figure, "Gemma 4 E2B", "P1"), gemma, places=digits)
            self.assertAlmostEqual(bar_value(figure, "Ministral 3 3B", "P3"), ministral, places=digits)
        distribution = chart(self.app, "global_distribution")
        self.assertEqual(distribution["layout"]["barmode"], "stack")
        for values in zip(*(trace_values(trace, "y") for trace in distribution["data"]), strict=True):
            self.assertAlmostEqual(sum(values), 100)

    def test_paired_prompts(self):
        self.app.segmented_control(key="filter_comparison_pairs").set_value([(P1, P3)]).run()
        self.assertFalse(self.app.exception)
        accuracy = chart(self.app, "prompt_accuracy")
        self.assertAlmostEqual(bar_value(accuracy, "Gemma 4 E2B", "P3 − P1"), -2.08, places=2)
        self.assertAlmostEqual(bar_value(accuracy, "Ministral 3 3B", "P3 − P1"), -12.51, places=2)
        gain, loss = chart(self.app, "prompt_transitions")["data"]
        self.assertTrue(all(value > 0 for value in trace_values(gain, "y")))
        self.assertTrue(all(value < 0 for value in trace_values(loss, "y")))
        self.assertEqual(self.app.dataframe[0].value.shape, (2, 8))

    def test_filters_for_knowledge_and_performance(self):
        filters = {
            "performance_model_id": [GEMMA], "performance_prompt_id": [P1],
            "category_model_id": [MINISTRAL], "category_prompt_id": [P3], "category_category": ["History"],
            "gap_prompt_id": [P1, P3], "gap_category": ["History"],
            "difficulty_model_id": [GEMMA], "difficulty_prompt_id": [P1], "difficulty_difficulty": ["hard"],
            "type_model_id": [MINISTRAL], "type_prompt_id": [P3], "type_type": ["boolean"],
        }
        for key, values in filters.items():
            widget = self.app.multiselect if key.endswith("_category") else self.app.segmented_control
            widget(key=f"filter_{key}").set_value(values)
        self.app.run()
        self.assertFalse(self.app.exception)
        line, = chart(self.app, "global_accuracy")["data"]
        self.assertEqual((line["name"], line["x"]), ("Gemma 4 E2B", ["P1"]))
        self.assertEqual(trace_values(chart(self.app, "category_rank_0")["data"][0], "y"), ["History"])
        heatmap = chart(self.app, "category_heatmap_0")["data"][0]
        self.assertEqual((heatmap["type"], heatmap["x"], heatmap["y"]), ("heatmap", ["P3"], ["History"]))
        self.assertEqual(heatmap["texttemplate"], "%{z:.2f} %")
        for index in range(2):
            gap = chart(self.app, f"category_gap_{index}")["data"][0]
            self.assertEqual(trace_values(gap, "y"), ["History"])
            self.assertIn("gemma", gap["hovertemplate"].lower())
            line, gemma, ministral = chart(self.app, f"category_connected_{index}")["data"]
            self.assertEqual(line["mode"], "lines")
            self.assertEqual((gemma["name"], ministral["name"]), ("Gemma", "Ministral"))
            self.assertEqual(line["x"][:2], [trace_values(gemma, "x")[0], trace_values(ministral, "x")[0]])
        bars, chance = chart(self.app, "difficulty_success")["data"]
        self.assertEqual(bars["x"], ["Difficile"])
        self.assertAlmostEqual(trace_values(chance, "y")[0], 27.20, places=2)
        self.app.segmented_control(key="filter_difficulty_type").set_value("boolean").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(trace_values(chart(self.app, "difficulty_success")["data"][-1], "y"), [50.0])
        for key, expected in (("type_success", 34.60), ("type_above_chance", -15.40), ("type_compliance", 58.05)):
            value = bar_value(chart(self.app, key), "Ministral 3 3B", "Vrai/faux")
            self.assertAlmostEqual(value, expected, places=2)

    def test_question_summaries_and_details(self):
        self.assertEqual([item.value.replace("\u202f", "") for item in self.app.metric][-4:], ["1379", "1278", "2633", "308"])
        self.assertEqual(trace_values(chart(self.app, "outcomes_shared")["data"][0], "y"), [308, 970])
        self.assertEqual(trace_values(chart(self.app, "outcomes_consensus_type")["data"][0], "y"), [207, 101])
        self.assertTrue(any("24,10 %" in item.value for item in self.app.caption))
        example = self.app.dataframe[-1].value.query("unanimous_wrong").iloc[0]
        self.app.multiselect(key="filter_outcomes_category").set_value([example.category])
        self.app.segmented_control(key="filter_outcomes_type").set_value(["boolean" if example.type == "Vrai/faux" else "multiple"])
        levels = {"Facile": "easy", "Intermédiaire": "medium", "Difficile": "hard"}
        self.app.segmented_control(key="filter_outcomes_difficulty").set_value([levels[example.difficulty]])
        self.app.segmented_control(key="filter_details_outcome").set_value(["all_incorrect"])
        self.app.segmented_control(key="filter_details_consensus").set_value("Oui")
        self.app.text_input(key="filter_details_search").set_value(example.question.swapcase()).run()
        self.assertFalse(self.app.exception)
        table = self.app.dataframe[-1].value
        self.assertEqual(table.shape, (1, 10))
        self.assertEqual(table.iloc[0].same_wrong_answer, example.same_wrong_answer)
        self.assertFalse(self.app.success)
        self.app.button(key="reveal_question").click().run()
        self.assertIn(example.correct_answer, self.app.success[0].value)
        self.assertTrue(any(f"**{example.same_wrong_answer}**" in item.value for item in self.app.info))
        self.app.button(key="reveal_question").click().run()
        self.assertFalse(self.app.success)
        self.app.text_input(key="filter_details_search").set_value("[texte-absent-").run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any(item.value.startswith("**0**") for item in self.app.markdown))
        self.assertTrue(any("Aucun résultat" in item.value for item in self.app.info))

    def test_empty_views_and_reset(self):
        for key in (
            "performance_model_id", "comparison_pairs", "category_prompt_id", "gap_prompt_id",
            "difficulty_difficulty", "type_type", "outcomes_type",
        ):
            self.app.segmented_control(key=f"filter_{key}").set_value([])
        self.app.segmented_control(key="filter_difficulty_type").set_value("multiple").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(self.app.get("plotly_chart")), 0)
        self.assertEqual(len([item for item in self.app.info if "Aucun résultat" in item.value]), 7)
        self.app.button(key="reset_performance").click().run()
        self.assertEqual(len(self.app.get("plotly_chart")), 4)
        self.assertEqual(self.app.segmented_control(key="filter_difficulty_type").value, "multiple")
        for scope in ("comparison", "category", "gap", "difficulty", "type", "outcomes_details"):
            self.app.button(key=f"reset_{scope}").click()
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(self.app.get("plotly_chart")), 30)
        self.assertEqual(active_filter(self.app.segmented_control, "filter_difficulty_type").value, "all")
        self.assertEqual(self.app.dataframe[-1].value.shape, (5290, 10))

    def test_question_change_hides_answer_and_reset_clears_details(self):
        questions = load_marts()["mart_question_outcomes"].sort_values(["category", "question", "question_id"])
        first, second = questions.iloc[0], questions.iloc[1]
        self.app.button(key="reveal_question").click().run()
        self.assertIn(first.correct_answer, self.app.success[0].value)
        self.app.selectbox(key="filter_details_question_id").set_value(second.question_id).run()
        self.assertFalse(self.app.success)
        self.assertEqual(self.app.button(key="reveal_question").label, "Révéler la réponse")
        self.app.button(key="reveal_question").click().run()
        self.assertIn(second.correct_answer, self.app.success[0].value)
        self.app.button(key="reset_outcomes_details").click().run()
        self.assertFalse(self.app.success)
        self.assertEqual(active_filter(self.app.selectbox, "filter_details_question_id").value, first.question_id)
