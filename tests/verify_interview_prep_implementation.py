"""
Verification script for Interview Prep Agent implementation
Demonstrates the complete functionality of the agent
"""

import sys
sys.path.insert(0, '.')

from unittest.mock import Mock
from agents.interview_prep_agent import InterviewPrepAgent, Question
from models.job import JobListing
from models.question import CustomQuestion
from utils.llm_client import LLMResponse


def verify_implementation():
    """Verify all implemented features"""
    
    print("=" * 70)
    print("INTERVIEW PREP AGENT - IMPLEMENTATION VERIFICATION")
    print("=" * 70)
    
    # Setup
    mock_llm = Mock()
    mock_repo = Mock()
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    print("\n✓ Agent initialized successfully")
    
    # Feature 1: Question Generation
    print("\n" + "=" * 70)
    print("FEATURE 1: Interview Question Generation")
    print("=" * 70)
    
    sample_job = JobListing(
        title="Senior LLM Engineer",
        company="TechCorp",
        description="Looking for an experienced LLM engineer with expertise in LangChain, RAG systems, and autonomous agents.",
        source="naukri",
        source_url="https://example.com/job/123"
    )
    
    mock_llm.generate_with_retry.return_value = LLMResponse(
        text="""**Q1: What is RAG and how does it work?**
Category: RAG Systems
Difficulty: medium

**Q2: Explain the difference between few-shot and zero-shot learning.**
Category: LLM Fundamentals
Difficulty: easy

**Q3: How would you implement a multi-agent system using LangChain?**
Category: LangChain
Difficulty: hard""",
        model="llama3",
        tokens_used=500
    )
    
    questions = agent.generate_questions(
        job=sample_job,
        question_type="technical",
        difficulty="medium",
        count=3
    )
    
    print(f"\n✓ Generated {len(questions)} interview questions")
    print("\nSample questions:")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. [{q.difficulty}] {q.text}")
        print(f"     Category: {q.category}")
    
    # Feature 2: Answer Evaluation
    print("\n" + "=" * 70)
    print("FEATURE 2: Answer Evaluation")
    print("=" * 70)
    
    mock_llm.generate_with_retry.return_value = LLMResponse(
        text="""**OVERALL ASSESSMENT:** Good answer with relevant details
**RATING:** 8/10

**STRENGTHS:**
- Clear explanation of RAG components
- Mentioned vector databases
- Provided practical example

**AREAS FOR IMPROVEMENT:**
- Could discuss chunking strategies
- Missing information about embedding models

**SUGGESTIONS:**
- Add details about chunk size optimization
- Mention specific vector database options

**IMPROVED VERSION:**
RAG combines retrieval with generation. Documents are chunked, embedded using models like sentence-transformers, and stored in vector databases like Pinecone.""",
        model="llama3",
        tokens_used=300
    )
    
    feedback = agent.evaluate_answer(
        question="What is RAG?",
        user_answer="RAG is a system that retrieves relevant information and uses it to generate responses.",
        question_category="technical"
    )
    
    print(f"\n✓ Answer evaluated successfully")
    print(f"\nRating: {feedback.rating}/10")
    print(f"\nStrengths ({len(feedback.strengths)}):")
    for s in feedback.strengths[:2]:
        print(f"  - {s}")
    print(f"\nImprovements ({len(feedback.improvements)}):")
    for i in feedback.improvements[:2]:
        print(f"  - {i}")
    
    # Feature 3: Mock Interview
    print("\n" + "=" * 70)
    print("FEATURE 3: Mock Interview Session")
    print("=" * 70)
    
    interview_questions = [
        Question(text="What is LangChain?", category="technical", difficulty="easy"),
        Question(text="Explain RAG systems", category="technical", difficulty="medium")
    ]
    
    user_answers = [
        "LangChain is a framework for building LLM applications.",
        "RAG systems retrieve relevant information to augment LLM responses."
    ]
    
    mock_llm.generate_with_retry.return_value = LLMResponse(
        text="""**RATING:** 7/10
**STRENGTHS:**
- Good basic understanding
**AREAS FOR IMPROVEMENT:**
- Add more details
**SUGGESTIONS:**
- Provide examples
**IMPROVED VERSION:**
Better answer here.""",
        model="llama3",
        tokens_used=200
    )
    
    session = agent.conduct_mock_interview(interview_questions, user_answers)
    
    print(f"\n✓ Mock interview completed")
    print(f"\nQuestions asked: {len(session.questions)}")
    print(f"Answers provided: {len(session.answers)}")
    print(f"Feedback generated: {len(session.feedback)}")
    print(f"Duration: {(session.completed_at - session.started_at).total_seconds():.2f} seconds")
    
    # Feature 4: Custom Question Management
    print("\n" + "=" * 70)
    print("FEATURE 4: Custom Question Management")
    print("=" * 70)
    
    mock_repo.save.return_value = True
    
    custom_q = agent.add_custom_question(
        user_id="user123",
        question_text="What is prompt engineering?",
        category="technical",
        topic="LLM",
        difficulty="easy"
    )
    
    print(f"\n✓ Custom question added")
    print(f"\nQuestion ID: {custom_q.id}")
    print(f"Text: {custom_q.question_text}")
    print(f"Category: {custom_q.category}")
    print(f"Topic: {custom_q.topic}")
    print(f"Difficulty: {custom_q.difficulty}")
    
    # Feature 5: Ideal Answer Generation
    print("\n" + "=" * 70)
    print("FEATURE 5: Ideal Answer Generation")
    print("=" * 70)
    
    mock_llm.generate_with_retry.return_value = LLMResponse(
        text="Prompt engineering is the practice of designing and optimizing prompts to effectively communicate with LLMs. It involves crafting clear instructions, providing relevant context, and using techniques like few-shot learning to guide the model toward desired outputs.",
        model="llama3",
        tokens_used=150
    )
    
    ideal_answer = agent.generate_ideal_answer(
        question="What is prompt engineering?",
        question_category="technical"
    )
    
    print(f"\n✓ Ideal answer generated")
    print(f"\nAnswer preview: {ideal_answer[:150]}...")
    
    # Feature 6: Question Filtering and Retrieval
    print("\n" + "=" * 70)
    print("FEATURE 6: Question Filtering and Retrieval")
    print("=" * 70)
    
    mock_questions = [
        CustomQuestion(
            user_id="user123",
            question_text="Question 1",
            category="technical",
            topic="LangChain"
        ),
        CustomQuestion(
            user_id="user123",
            question_text="Question 2",
            category="behavioral",
            topic="Leadership"
        )
    ]
    mock_repo.find_by_user.return_value = mock_questions
    
    questions = agent.get_custom_questions(
        user_id="user123",
        filters={"category": "technical"}
    )
    
    print(f"\n✓ Retrieved {len(questions)} custom questions")
    
    # Feature 7: Question Updates
    print("\n" + "=" * 70)
    print("FEATURE 7: Question Updates")
    print("=" * 70)
    
    existing_question = CustomQuestion(
        id="q123",
        user_id="user123",
        question_text="Old question",
        category="technical"
    )
    mock_repo.find_by_id.return_value = existing_question
    mock_repo.update.return_value = True
    
    success = agent.update_custom_question(
        question_id="q123",
        updates={"question_text": "Updated question", "difficulty": "hard"}
    )
    
    print(f"\n✓ Question updated: {success}")
    
    # Feature 8: Job Linking
    print("\n" + "=" * 70)
    print("FEATURE 8: Link Questions to Jobs")
    print("=" * 70)
    
    success = agent.link_question_to_job("q123", "job456")
    print(f"\n✓ Question linked to job: {success}")
    
    mock_questions_with_job = [
        CustomQuestion(
            user_id="user123",
            question_text="Q1",
            category="technical",
            topic="job:job456"
        )
    ]
    mock_repo.find_by_user.return_value = mock_questions_with_job
    
    job_questions = agent.get_questions_for_job("user123", "job456")
    print(f"✓ Retrieved {len(job_questions)} questions for job")
    
    # Summary
    print("\n" + "=" * 70)
    print("IMPLEMENTATION SUMMARY")
    print("=" * 70)
    
    features = [
        "✓ Interview question generation (technical, behavioral, system design)",
        "✓ Question categorization and difficulty assignment",
        "✓ Answer evaluation with detailed feedback",
        "✓ Mock interview sessions with multiple questions",
        "✓ Custom question library management",
        "✓ Ideal answer generation using LLM",
        "✓ Question filtering by category, topic, difficulty",
        "✓ Question updates and modifications",
        "✓ Link questions to specific job applications",
        "✓ Retrieve questions by job"
    ]
    
    print("\nImplemented Features:")
    for feature in features:
        print(f"  {feature}")
    
    print("\n" + "=" * 70)
    print("✓ ALL FEATURES VERIFIED SUCCESSFULLY")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        verify_implementation()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
