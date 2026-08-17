"""Tests for RAG Prompt Module."""

import pytest

from langchain_core.documents import Document

from app.config.constants import NOT_AVAILABLE_MESSAGE_MARATHI
from app.prompts.rag_prompt import HUMAN_TEMPLATE, SYSTEM_PROMPT, PromptService


class TestPromptService:
    """Tests for the PromptService class."""

    def setup_method(self):
        """Create a PromptService for each test."""
        self.service = PromptService()

    def test_prompt_has_context_variable(self):
        """Test that the prompt template has a 'context' input variable."""
        prompt = self.service.get_prompt()
        input_vars = prompt.input_variables
        assert "context" in input_vars

    def test_prompt_has_question_variable(self):
        """Test that the prompt template has a 'question' input variable."""
        prompt = self.service.get_prompt()
        input_vars = prompt.input_variables
        assert "question" in input_vars

    def test_system_prompt_contains_refusal_message(self):
        """Test that the system prompt includes the refusal instruction."""
        assert NOT_AVAILABLE_MESSAGE_MARATHI in SYSTEM_PROMPT

    def test_system_prompt_contains_page_citation_instruction(self):
        """Test that the system prompt instructs page citation."""
        assert "पृष्ठ" in SYSTEM_PROMPT

    def test_system_prompt_forbids_outside_knowledge(self):
        """Test that the prompt explicitly forbids outside knowledge."""
        assert "बाहेरच" in SYSTEM_PROMPT or "बाहेरचे" in SYSTEM_PROMPT

    def test_format_context_with_documents(self):
        """Test context formatting with sample documents."""
        docs = [
            Document(
                page_content="मराठी भाषा सुंदर आहे.",
                metadata={"page_number": 5, "chapter": "intro"},
            ),
            Document(
                page_content="गणित शिकणे महत्त्वाचे आहे.",
                metadata={"page_number": 12, "chapter": "math"},
            ),
        ]
        context = self.service.format_context(docs)
        assert "पृष्ठ: 5" in context
        assert "पृष्ठ: 12" in context
        assert "मराठी भाषा" in context
        assert "गणित शिकणे" in context

    def test_format_context_empty_documents(self):
        """Test context formatting with no documents."""
        context = self.service.format_context([])
        assert "उपलब्ध नाही" in context

    def test_prompt_can_be_formatted(self):
        """Test that the prompt can be successfully formatted with values."""
        prompt = self.service.get_prompt()
        messages = prompt.format_messages(
            context="Some context text",
            question="What is this about?",
        )
        assert len(messages) == 2  # system + human
        assert "Some context text" in messages[0].content
        assert "What is this about?" in messages[1].content
