# v1.8.10 Submit Transaction Plan

Status: coded; production acceptance not_run.

The successful submit path pre-generates run/conversation/job identifiers, writes the run, conversation, user message, and assistant placeholder in one database transaction, commits, then enqueues the explicit RQ job id. Enqueue failure uses one compensating write transaction. The regression budget is at most five transactions and three commits.

