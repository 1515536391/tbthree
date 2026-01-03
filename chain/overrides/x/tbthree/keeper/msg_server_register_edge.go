package keeper

import (
	"context"
	"time"

	errorsmod "cosmossdk.io/errors"
	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"

	"tbthree/x/tbthree/types"
)

func (k msgServer) RegisterEdge(goCtx context.Context, msg *types.MsgRegisterEdge) (*types.MsgRegisterEdgeResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	// basic signer validation
	if _, err := sdk.AccAddressFromBech32(msg.Creator); err != nil {
		return nil, errorsmod.Wrap(sdkerrors.ErrInvalidAddress, err.Error())
	}

	if msg.EdgeAddr == "" {
		return nil, errorsmod.Wrap(types.ErrInvalidRequest, "edge_addr is required")
	}
	if msg.Region == "" {
		return nil, errorsmod.Wrap(types.ErrInvalidRequest, "region is required")
	}

	if _, found := k.GetEdge(ctx, msg.EdgeAddr); found {
		return nil, errorsmod.Wrap(types.ErrEdgeAlreadyRegistered, msg.EdgeAddr)
	}

	now := time.Now().Unix()

	// Defaults:
	// - subjective logic: b=0,d=0,u=1 (scaled by FPScale)
	// - HMM: uniform distribution
	hmmT := uint64(types.HMMScale / 3)
	hmmS := uint64(types.HMMScale / 3)
	hmmM := uint64(types.HMMScale) - hmmT - hmmS

	edge := types.Edge{
		EdgeAddr: msg.EdgeAddr,
		CreatorAddr: msg.Creator,
		Region: msg.Region,
		Status: types.EdgeStatusActive,
		PriorityPenalty: 0,

		// NOTE: edge.proto uses bd_score/bu_score/du_score/dud_score.
		// We treat them as (b,u,d,score) scaled by FPScale for compatibility
		// with the existing reputation logic & frontend.
		BdScore: 0,
		BuScore: uint64(types.FPScale),
		DuScore: 0,
		DudScore: 0,

		HmmProbT: hmmT,
		HmmProbS: hmmS,
		HmmProbM: hmmM,

		EvidencePos: 0,
		EvidenceNeg: 0,
		PendingProposalId: "",
		UpdatedAt: now,

		// ignite maps usually include a trailing "creator" field on the stored object
		Creator: msg.Creator,
	}

	k.SetEdge(ctx, edge)
	return &types.MsgRegisterEdgeResponse{}, nil
}
