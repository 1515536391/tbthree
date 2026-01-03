package keeper

import (
	"context"

	"tbthree/x/tbthree/types"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func (k msgServer) ReportConsensusEvent(goCtx context.Context, msg *types.MsgReportConsensusEvent) (*types.MsgReportConsensusEventResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	edge, found := k.GetEdge(ctx, msg.EdgeAddr)
	if !found {
		return nil, types.ErrEdgeNotFound
	}

	edge.MissedVotes += msg.MissedVotes
	edge.DoubleSigns += msg.DoubleSigns
	edge.BlockParticipationPermil = msg.BlockParticipationPermil

	obs := 0
	if msg.DoubleSigns > 0 {
		obs = 2
	} else if msg.MissedVotes > 5 || msg.BlockParticipationPermil < 200 {
		obs = 1
	}

	k.UpdateReputation(ctx, &edge, obs, "consensus")
	k.SetEdge(ctx, edge)

	return &types.MsgReportConsensusEventResponse{}, nil
}
