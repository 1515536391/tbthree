package keeper

import (
	"context"

	"tbthree/x/tbthree/types"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func (k msgServer) SubmitTaskFeedback(goCtx context.Context, msg *types.MsgSubmitTaskFeedback) (*types.MsgSubmitTaskFeedbackResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	task, found := k.GetTask(ctx, msg.TaskId)
	if !found {
		return nil, types.ErrTaskNotFound
	}
	if task.VehicleAddr != msg.Creator {
		return nil, types.ErrTaskInvalidOwner
	}

	edge, eFound := k.GetEdge(ctx, task.ChosenEdgeAddr)
	if eFound {
		obs := 0
		if !msg.Accepted {
			obs = 2
			edge.Complaints += 1
		} else {
			edge.Correct += 1
		}
		k.UpdateReputation(ctx, &edge, obs, "vehicleFeedback")
		k.SetEdge(ctx, edge)
	}

	return &types.MsgSubmitTaskFeedbackResponse{}, nil
}
