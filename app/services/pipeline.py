"""Compatibility facade for the modular-monolith meeting feature.

New code should depend on app.features.meeting.application.pipeline.
This module remains temporarily stable for existing integrations/tests.
"""
from app.features.meeting.application.pipeline import IntakeQuestion, QuestionPipeline, LLMCategory, LLMNominee

__all__ = ["IntakeQuestion", "QuestionPipeline", "LLMCategory", "LLMNominee"]
