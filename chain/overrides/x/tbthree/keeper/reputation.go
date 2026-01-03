package keeper

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	sdk "github.com/cosmos/cosmos-sdk/types"

	"tbthree/x/tbthree/types"
)

// Fixed-point helpers (scale = types.FPScale)
const fpScale int64 = types.FPScale

func fpMul(a, b int64) int64 { return (a * b) / fpScale }
func fpDiv(a, b int64) int64 {
	if b == 0 {
		return 0
	}
	return (a * fpScale) / b
}

func clampNonNeg(a int64) int64 {
	if a < 0 {
		return 0
	}
	return a
}

func clampU64(a int64) uint64 {
	return uint64(clampNonNeg(a))
}

// subjectiveFromEvidence converts (r,s) evidence into subjective logic opinion (b,d,u), all scaled by fpScale.
//
// We keep a small prior to avoid division-by-zero and start from (b=0,d=0,u=1).
func subjectiveFromEvidence(r, s int64) (b, d, u int64) {
	if r < 0 {
		r = 0
	}
	if s < 0 {
		s = 0
	}
	const prior = int64(2) // Dirichlet prior strength
	total := r + s + prior
	if total <= 0 {
		return 0, 0, fpScale
	}
	b = fpDiv(r, total)
	d = fpDiv(s, total)
	u = fpDiv(prior, total)
	// safety: enforce non-negative
	return clampNonNeg(b), clampNonNeg(d), clampNonNeg(u)
}

// scoreFromOpinion uses the same front-end convention shown on the dashboard: score = b + 0.5*u.
func scoreFromOpinion(b, u int64) int64 {
	return clampNonNeg(b + u/2)
}

// hmmUpdate updates an HMM belief vector (pT,pS,pM) using observation obs.
//
// p* are scaled by types.HMMScale.
func hmmUpdate(pT, pS, pM int64, obs int) (nT, nS, nM int64) {
	// transition matrix A (rows sum to HMMScale)
	A := [3][3]int64{
		{900000, 80000, 20000},
		{100000, 800000, 100000},
		{20000, 80000, 900000},
	}
	// emission matrix B (rows sum to HMMScale)
	B := [3][3]int64{
		{850000, 120000, 30000},
		{200000, 600000, 200000},
		{30000, 120000, 850000},
	}

	const hmmScale int64 = types.HMMScale

	// predict: p' = p * A
	pT2 := (pT*A[0][0] + pS*A[1][0] + pM*A[2][0]) / hmmScale
	pS2 := (pT*A[0][1] + pS*A[1][1] + pM*A[2][1]) / hmmScale
	pM2 := (pT*A[0][2] + pS*A[1][2] + pM*A[2][2]) / hmmScale

	// update with emission
	eT := B[0][obs]
	eS := B[1][obs]
	eM := B[2][obs]

	nT = (pT2 * eT) / hmmScale
	nS = (pS2 * eS) / hmmScale
	nM = (pM2 * eM) / hmmScale

	// normalize
	sum := nT + nS + nM
	if sum <= 0 {
		return hmmScale / 3, hmmScale / 3, hmmScale - 2*(hmmScale/3)
	}
	nT = (nT * hmmScale) / sum
	nS = (nS * hmmScale) / sum
	nM = hmmScale - nT - nS
	return
}

// UpdateReputation updates an edge's reputation based on observation (0=good, 1=anomaly, 2=timeout).
// It updates both subjective logic (bd_score/du_score/bu_score/dud_score) and HMM probs.
func (k Keeper) UpdateReputation(ctx sdk.Context, edge *types.Edge, obs int, reason string) {
	// 1) update evidence
	if obs == 0 {
		edge.EvidencePos += 1
	} else {
		edge.EvidenceNeg += 1
	}

	// 2) subjective logic b/d/u (fixed-point)
	b, d, u := subjectiveFromEvidence(int64(edge.EvidencePos), int64(edge.EvidenceNeg))
	score := scoreFromOpinion(b, u)

	// Store them into existing on-chain fields.
	// NOTE: proto uses bd_score/bu_score/du_score/dud_score.
	// We map them as: bd_score=b, du_score=d, bu_score=u, dud_score=score.
	edge.BdScore = clampU64(b)
	edge.DuScore = clampU64(d)
	edge.BuScore = clampU64(u)
	edge.DudScore = clampU64(score)

	// 3) HMM update (fixed-point scale types.HMMScale)
	pT := int64(edge.HmmProbT)
	pS := int64(edge.HmmProbS)
	pM := int64(edge.HmmProbM)
	nT, nS, nM := hmmUpdate(pT, pS, pM, obs)
	edge.HmmProbT = clampU64(nT)
	edge.HmmProbS = clampU64(nS)
	edge.HmmProbM = clampU64(nM)

	// 4) update timestamps
	edge.UpdatedAt = ctx.BlockTime().Unix()

	// 5) governance proposal trigger (best-effort)
	k.maybeCreateGovernanceProposal(ctx, edge, score, reason)

	// 6) store propagation snapshot hash (optional)
	_ = k.reputationSnapshotHash(*edge)
}

func (k Keeper) maybeCreateGovernanceProposal(ctx sdk.Context, edge *types.Edge, score int64, reason string) {
	// if there is already a pending proposal, do nothing
	if edge.PendingProposalId != "" {
		return
	}

	// threshold: 0.30 in fixed-point
	threshold := fpScale * 3 / 10
	if score >= threshold {
		return
	}

	// Create a proposal id (deterministic enough for local demo)
	pid := fmt.Sprintf("P-%s-%d", edge.EdgeAddr, time.Now().UnixNano())

	// Encode the "action" into reason (proto currently has no Action field)
	reasonStr := fmt.Sprintf("auto: score<thr (score=%d, thr=%d); %s", score, threshold, reason)

	prop := types.GovernanceProposal{
		ProposalId: pid,
		EdgeAddr:   edge.EdgeAddr,
		Status:     types.ProposalStatusPending,
		Reason:     reasonStr,
		ApprovedBy: "",
		DecidedAt:  0,
		Creator:    types.AdminModuleName,
	}

	k.SetGovernanceProposal(ctx, prop)
	edge.PendingProposalId = pid
}

func (k Keeper) reputationSnapshotHash(edge types.Edge) string {
	payload := fmt.Sprintf(
		"edge=%s|b=%d|d=%d|u=%d|score=%d|pT=%d|pS=%d|pM=%d|ePos=%d|eNeg=%d|t=%d",
		edge.EdgeAddr,
		edge.BdScore,
		edge.DuScore,
		edge.BuScore,
		edge.DudScore,
		edge.HmmProbT,
		edge.HmmProbS,
		edge.HmmProbM,
		edge.EvidencePos,
		edge.EvidenceNeg,
		edge.UpdatedAt,
	)
	h := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(h[:])
}
