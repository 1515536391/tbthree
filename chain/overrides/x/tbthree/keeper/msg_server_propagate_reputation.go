package keeper

import (
	"context"
	"fmt"

	"tbthree/x/tbthree/types"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func (k msgServer) PropagateReputation(goCtx context.Context, msg *types.MsgPropagateReputation) (*types.MsgPropagateReputationResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	edge, found := k.GetEdge(ctx, msg.EdgeAddr)
	if !found {
		return nil, types.ErrEdgeNotFound
	}

	pid := fmt.Sprintf("%d", k.NextSeq(ctx, "propagation"))
	repHash := ReputationSnapshotHash(edge)

	prop := types.ReputationPropagation{
		PropagationId:  pid,
		EdgeAddr:       msg.EdgeAddr,
		FromRegion:     msg.FromRegion,
		ToRegion:       msg.ToRegion,
		RepSnapshotHash: repHash,
		Reason:         msg.Reason,
		Height:         uint64(ctx.BlockHeight()),
		CreatedAt:      ctx.BlockTime().Unix(),
	}

	k.SetReputationPropagation(ctx, prop)
	return &types.MsgPropagateReputationResponse{}, nil
}
