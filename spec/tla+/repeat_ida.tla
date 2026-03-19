---- MODULE repeat_ida ----
EXTENDS Naturals, TLC

CONSTANTS MaxIterations, Null

VARIABLES phase, receipts, currentReceipt, decision, diagnostics, adjustment, seq, replayMode, committed, iteration

(* --algorithm structure *)
VARIABLE Init, ReceiveCertifiedReceipt, Diagnose, EmitAdjustment, Verify, Commit, FailClosed, Next

Phases == {"INIT", "RECEIPT_CERTIFIED", "DIAGNOSE", "ADJUST", "VERIFY", "COMMITTED", "HALT"}

Invariants == {
  NoOrphanAdjustment, DecisionAuthoritative, NoDuplicateCommit, NoReplayMutation, DeterministicAdvance, BoundedIteration
}

Liveness == {
  EventuallyVerifyOrFail, EventuallyCommitOrHalt
}

HelperPredicates == {
  HasCertifiedReceipt, AdjustmentBoundToReceipt, DecisionFromReceiptOnly, VerifiedBeforeCommit, ReplayNonMutating, 
  WithinIterationBound, AdvanceBySeqOrChain, Final, Exists, ProvisionalActionAllowed, CommittedActionAllowed
}

Final(receipt) == receipt \in AVS.committed /\ proofVerified(receipt)
Exists(receipt) == Final(receipt)
ProvisionalActionAllowed == TRUE (* Placeholder definition *)
CommittedActionAllowed == TRUE (* Placeholder definition *)

Spec == Init /\ [][][Next]_vars