package types

// Fixed point scale for deterministic on-chain math.
// All reputation-related decimals are stored as int64 scaled by 1e6.
const FPScale int64 = 1_000_000

// Edge statuses
const (
	EdgeStatusActive          = "ACTIVE"
	EdgeStatusTaskFrozen      = "TASK_FROZEN"
	EdgeStatusConsensusFrozen = "CONSENSUS_FROZEN"
)

// Task statuses
const (
	TaskStatusCreated  = "CREATED"
	TaskStatusAssigned = "ASSIGNED"
	TaskStatusRunning  = "RUNNING"
	TaskStatusFinished = "FINISHED"
	TaskStatusFailed   = "FAILED"
)

// Governance proposal statuses
const (
	ProposalStatusPending  = "PENDING"
	ProposalStatusApproved = "APPROVED"
	ProposalStatusRejected = "REJECTED"
)

// Governance actions
const (
	ActionWeightDown      = "WEIGHT_DOWN"
	ActionTaskFreeze      = "TASK_FREEZE"
	ActionConsensusFreeze = "CONSENSUS_FREEZE"
)
