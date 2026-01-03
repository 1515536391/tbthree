package keeper

import (
	"context"
	"strings"

	"tbthree/x/tbthree/types"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func (k msgServer) RejectProposal(goCtx context.Context, msg *types.MsgRejectProposal) (*types.MsgRejectProposalResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	admin, ok := k.GetAdmin(ctx)
	if !ok {
		return nil, types.ErrNotAuthorized
	}
	if msg.Creator != admin {
		return nil, types.ErrNotAuthorized
	}

	prop, found := k.GetGovernanceProposal(ctx, msg.ProposalId)
	if !found {
		return nil, types.ErrProposalNotFound
	}
	if strings.ToUpper(prop.Status) != types.ProposalStatusPending {
		return nil, types.ErrProposalNotPending
	}

	edge, eFound := k.GetEdge(ctx, prop.EdgeAddr)
	if eFound {
		if edge.PendingProposalId == prop.ProposalId {
			edge.PendingProposalId = ""
			k.SetEdge(ctx, edge)
		}
	}

	prop.Status = types.ProposalStatusRejected
	prop.ApprovedBy = msg.Creator
	prop.DecidedAt = ctx.BlockTime().Unix()
	// store reject reason in prop.Reason (append)
	if msg.Reason != "" {
		prop.Reason = prop.Reason + " | reject:" + msg.Reason
	}
	k.SetGovernanceProposal(ctx, prop)

	return &types.MsgRejectProposalResponse{}, nil
}
