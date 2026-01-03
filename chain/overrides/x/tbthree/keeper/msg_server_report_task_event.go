package keeper

import (
	"context"

	"tbthree/x/tbthree/types"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func (k msgServer) ReportTaskEvent(goCtx context.Context, msg *types.MsgReportTaskEvent) (*types.MsgReportTaskEventResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	edge, found := k.GetEdge(ctx, msg.EdgeAddr)
	if !found {
		return nil, types.ErrEdgeNotFound
	}

	if msg.OnTime {
		edge.OnTime += 1
	}
	if msg.Correct {
		edge.Correct += 1
	}
	if msg.ResourceAnomaly {
		edge.ResourceAnomaly += 1
		edge.Anomalies += 1
	}
	if msg.Timeout {
		edge.Timeout += 1
	}

	obs := 0
	if msg.Timeout || !msg.Correct {
		obs = 2
	} else if msg.ResourceAnomaly {
		obs = 1
	}

	k.UpdateReputation(ctx, &edge, obs, "taskEvent")
	k.SetEdge(ctx, edge)

	return &types.MsgReportTaskEventResponse{}, nil
}
