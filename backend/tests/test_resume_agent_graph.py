import unittest
from unittest.mock import patch

from app.services.ai.agent import plan_resume_agent_turn
from app.services.ai.schemas import ResumeChatIntentResult


def intent(name: str) -> ResumeChatIntentResult:
    return ResumeChatIntentResult(
        intent=name,
        change_scope="partial" if name == "propose_change" else "none",
        target_sections=["summary"] if name == "propose_change" else [],
    )


class ResumeAgentGraphTest(unittest.TestCase):
    def plan(self, intent_name: str, *, pending: bool = False):
        with patch(
            "app.services.ai.agent.resume_chat_intent_chain",
            return_value=intent(intent_name),
        ):
            return plan_resume_agent_turn(
                {"user_message": "test"},
                pending_change_available=pending,
            )

    def test_routes_questions_to_answer_tool(self) -> None:
        plan = self.plan("answer")

        self.assertEqual(plan.route, "answer")
        self.assertFalse(plan.requires_confirmation)

    def test_routes_edits_to_proposal_tool(self) -> None:
        plan = self.plan("propose_change")

        self.assertEqual(plan.route, "propose_change")
        self.assertTrue(plan.requires_confirmation)
        self.assertEqual(plan.intent.target_sections, ["summary"])

    def test_allows_apply_only_when_a_pending_change_exists(self) -> None:
        self.assertEqual(self.plan("confirm_change", pending=True).route, "apply_change")
        self.assertEqual(self.plan("confirm_change", pending=False).route, "missing_pending_change")

    def test_allows_reject_only_when_a_pending_change_exists(self) -> None:
        self.assertEqual(self.plan("reject_change", pending=True).route, "reject_change")
        self.assertEqual(self.plan("reject_change", pending=False).route, "missing_pending_change")


if __name__ == "__main__":
    unittest.main()
