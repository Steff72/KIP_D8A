
The following is a set of rules and guidelines that Codex (AI development assistant) must follow when contributing to the D8A Coin project. These rules ensure that Codex’s involvement leads to a consistent, high-quality codebase and documentation, and that the human developer remains in control and informed:
	1.	Maintain the Project Plan: After any significant change or addition to the codebase, Codex must update the concept.md document to reflect those changes. This means adjusting design descriptions, data flows, or class details in the technical specification so it stays current with the implementation.
	2.	Keep a Developer Log: Codex should continuously append entries to experience.md to document the development process. This log should record what was done, any problems encountered, how they were solved, and insights gained. Entries should be written in a reflective, first-person tone (as if by the developer), and include details on how Codex was used or how the approach was adjusted.
	3.	Follow Test-Driven Development (TDD): Codex must adhere to the TDD methodology strictly:
	•	Write or propose unit tests for new functionality before implementing the code (or ensure tests are already written by the user).
	•	Only write the minimal code needed to pass the tests.
	•	Ensure all tests pass before moving on. Do not write large untested code blocks.
	•	If a test fails, focus on that failure and fix the code (or adjust the test if the test is wrong) before anything else.
	4.	PEP8 Compliance and Clean Code: All Python code written by Codex must follow PEP8 style guidelines (proper naming, spacing, line length, etc.) and be clean and readable. This includes using meaningful variable and function names, adding comments or docstrings for clarity when needed, and avoiding overly complex or nested logic that harms readability. The code should look as if written by a professional Python developer.
	5.	Atomic Commits with Descriptive Messages: Codex should assist in maintaining a clean Git commit history:
	•	Break changes into atomic commits (each commit has one focused purpose, e.g., “Add test for transaction update” or “Implement Block.is_valid_block validation checks”).
	•	Each commit message should be descriptive, explaining what was done in imperative mood (e.g., “Implement transaction signature verification in Wallet.verify”).
	•	Do not mix unrelated changes in a single commit. If Codex generates code for multiple features, separate them into multiple commits.
	•	If using an automated tool to commit, ensure the message is edited to be clear and specific.
	6.	Preserve Versioning and Milestones: Codex should respect the project milestone plan:
	•	Work on tasks in the order defined by the milestones (unless directed otherwise by the developer).
	•	Ensure that once a milestone’s features are complete and tests pass, the code is stable (all tests green) and can be tagged for that version.
	•	Avoid introducing milestone-4 or 5 features before earlier milestones are finished, to keep the project progress organized.
	7.	No Overwrite without Understanding: Codex should not delete or drastically refactor existing code unless it’s part of an intentional change discussed in the plan. When refactoring, do it in small steps, run tests after each, and update documentation (concept.md) if any class/method behavior changes.
	8.	Security and Integrity: When generating code for cryptographic and blockchain-related functionality, Codex must follow the intended algorithms exactly:
	•	Use reliable libraries for cryptography (do not invent insecure methods).
	•	Do not weaken the proof-of-work difficulty or bypass validation checks just to satisfy tests; always implement the full check.
	•	If unsure, prefer to ask (via comments or partial implementation) rather than guess and risk a security hole.
	9.	Ask for Clarification When Needed: If requirements in concept.md or tests are ambiguous, Codex can flag this in comments or seek clarification from the developer (in practice, this might mean the developer will adjust the prompt or tests). It is better to pause and ensure correctness than to implement a wrong assumption.
	10.	Consistency with Design: All code contributions by Codex should stay consistent with the architecture and design outlined in concept.md. For example, do not introduce global variables where the design says to encapsulate state in classes, and do not bypass the PubNub interface if the design expects it. If a change in design seems necessary, discuss (via experience.md log entry or developer prompt) and update concept.md accordingly before implementing.

By following these rules, Codex will act as a disciplined AI pair programmer. These guidelines ensure the development remains on track, the codebase stays maintainable, and the collaboration between the human developer and AI yields a successful implementation of D8A Coin.
