# v1.8.10 Submit Transaction Plan

Status: passed for transaction budget and production profile.

The successful submit path pre-generates run/conversation/job identifiers, writes the run, conversation, user message, and assistant placeholder in one database transaction, commits, then enqueues the explicit RQ job id. Enqueue failure uses one compensating write transaction. The regression budget is at most five transactions and three commits.

Measured result: 16 transactions/16 commits before; 4 transactions/1 commit after. The remaining three transactions are read-only guards and end with rollback rather than commit.
