---- MODULE repeat_ida ----
EXTENDS Naturals, TLC

CONSTANTS MaxIterations, Null, Receipts

VARIABLES phase, receipts, currentReceipt, decision, diagnostics, adjustment,
          seq, replayMode, committed, iteration

vars == <<phase, receipts, currentReceipt, decision, diagnostics, adjustment,
          seq, replayMode, committed, iteration>>

Phases == {"INIT", "RECEIPT_CERTIFIED", "DIAGNOSE", "ADJUST", "VERIFY", "COMMITTED", "HALT"}
Decisions == {Null, "PROVISIONAL", "COMMIT", "FAIL_CLOSED"}

Init ==
  /\\ phase = "INIT"
  /\\ receipts = {}
  /\\ currentReceipt = Null
  /\\ decision = Null
  /\\ diagnostics = <<>>
  /\\ adjustment = Null
  /\\ seq = 0
  /\\ replayMode = FALSE
  /\\ committed = {}
  /\\ iteration = 0

HasCertifiedReceipt == currentReceipt # Null /\\ currentReceipt \in receipts
AdjustmentBoundToReceipt == adjustment # Null => HasCertifiedReceipt
DecisionFromReceiptOnly == decision \in {Null, "FAIL_CLOSED"} \/ (HasCertifiedReceipt /\\ decision \in {"PROVISIONAL", "COMMIT"})
VerifiedBeforeCommit == phase = "COMMITTED" => decision = "COMMIT" /\\ HasCertifiedReceipt
ReplayNonMutating == replayMode => adjustment = Null /\\ decision # "COMMIT"
WithinIterationBound == iteration <= MaxIterations
AdvanceBySeqOrChain == seq = iteration
Final == phase \in {"COMMITTED", "HALT"}
Exists(receipt) == receipt \in receipts
ProvisionalActionAllowed == phase = "ADJUST" /\\ HasCertifiedReceipt /\\ decision = "PROVISIONAL"
CommittedActionAllowed == phase = "VERIFY" /\\ HasCertifiedReceipt /\\ decision = "COMMIT"

ReceiveCertifiedReceipt ==
  /\\ phase = "INIT" /\\ Receipts # {} /\\
      \\E receipt \in Receipts: currentReceipt' = receipt
  /\\ receipts' = receipts \/ {currentReceipt'}
  /\\ phase' = "RECEIPT_CERTIFIED"
  /\\ UNCHANGED <<decision, diagnostics, adjustment, seq, replayMode, committed, iteration>>

Diagnose ==
  /\\ phase = "RECEIPT_CERTIFIED" /\\ HasCertifiedReceipt
  /\\ phase' = "DIAGNOSE" /\\ diagnostics' = <<"RECEIPT_CERTIFIED">>
  /\\ UNCHANGED <<receipts, currentReceipt, decision, adjustment, seq, replayMode, committed, iteration>>

EmitAdjustment ==
  /\\ phase = "DIAGNOSE" /\\ HasCertifiedReceipt /\\ ~replayMode
  /\\ phase' = "ADJUST" /\\ adjustment' = currentReceipt
  /\\ decision' = "PROVISIONAL" /\\ seq' = seq + 1
  /\\ UNCHANGED <<receipts, currentReceipt, diagnostics, replayMode, committed, iteration>>

Verify ==
  /\\ phase = "ADJUST" /\\ ProvisionalActionAllowed
  /\\ phase' = "VERIFY" /\\ decision' = "COMMIT" /\\ seq' = seq + 1
  /\\ UNCHANGED <<receipts, currentReceipt, diagnostics, adjustment, replayMode, committed, iteration>>

Commit ==
  /\\ phase = "VERIFY" /\\ CommittedActionAllowed /\\ iteration < MaxIterations
  /\\ phase' = "COMMITTED" /\\ committed' = committed \/ {currentReceipt}
  /\\ iteration' = iteration + 1
  /\\ UNCHANGED <<receipts, currentReceipt, decision, diagnostics, adjustment, seq, replayMode>>

FailClosed ==
  /\\ (iteration >= MaxIterations \/ replayMode \/ phase = "VERIFY" /\\ ~HasCertifiedReceipt)
  /\\ phase' = "HALT" /\\ decision' = "FAIL_CLOSED"
  /\\ UNCHANGED <<receipts, currentReceipt, diagnostics, adjustment, seq, replayMode, committed, iteration>>

Next == ReceiveCertifiedReceipt \/ Diagnose \/ EmitAdjustment \/ Verify \/ Commit \/ FailClosed

NoOrphanAdjustment == adjustment # Null => HasCertifiedReceipt
DecisionAuthoritative == decision = "COMMIT" => HasCertifiedReceipt
NoDuplicateCommit == committed \subseteq receipts
NoReplayMutation == ReplayNonMutating
DeterministicAdvance == AdvanceBySeqOrChain
BoundedIteration == WithinIterationBound

Invariants == {NoOrphanAdjustment, DecisionAuthoritative, NoDuplicateCommit,
  NoReplayMutation, DeterministicAdvance, BoundedIteration}
Liveness == {EventuallyVerifyOrFail, EventuallyCommitOrHalt}
EventuallyVerifyOrFail == [] (phase = "ADJUST" => <> (phase = "VERIFY" \/ phase = "HALT"))
EventuallyCommitOrHalt == [] (phase = "VERIFY" => <> (phase = "COMMITTED" \/ phase = "HALT"))

Spec == Init /\\ [][Next]_vars
====
