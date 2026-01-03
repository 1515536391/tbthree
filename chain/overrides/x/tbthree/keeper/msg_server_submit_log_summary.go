package keeper

import (
	"context"
	"strings"

	"tbthree/x/tbthree/types"

	sdk "github.com/cosmos/cosmos-sdk/types"
)

func (k msgServer) SubmitLogSummary(goCtx context.Context, msg *types.MsgSubmitLogSummary) (*types.MsgSubmitLogSummaryResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	task, found := k.GetTask(ctx, msg.TaskId)
	if !found {
		return nil, types.ErrTaskNotFound
	}
	if task.ChosenEdgeAddr != msg.Creator {
		return nil, types.ErrNotAuthorized
	}
	edge, eFound := k.GetEdge(ctx, task.ChosenEdgeAddr)
	if !eFound {
		return nil, types.ErrEdgeNotFound
	}
	if edge.Status == types.EdgeStatusTaskFrozen {
		return nil, types.ErrEdgeTaskFrozen
	}

	// store log summary on chain
	ls := types.LogSummary{
		LogHash:     msg.LogHash,
		TaskId:      msg.TaskId,
		EdgeAddr:    task.ChosenEdgeAddr,
		Stage:       msg.Stage,
		Ts:          msg.Ts,
		CpuMs:       msg.CpuMs,
		MemMbPeak:   msg.MemMbPeak,
		NetKb:       msg.NetKb,
		LatencyMs:   msg.LatencyMs,
		ResultHash:  msg.ResultHash,
	}
	k.SetLogSummary(ctx, ls)

	// update task logHashes (store as ';' separated string)
	if strings.TrimSpace(task.LogHashes) == "" {
		task.LogHashes = msg.LogHash
	} else {
		task.LogHashes = task.LogHashes + ";" + msg.LogHash
	}

	// update task status best-effort
	stage := strings.ToUpper(msg.Stage)
	if stage == "RECV" {
		task.Status = types.TaskStatusRunning
	}
	if stage == "RESULT" {
		task.Status = types.TaskStatusFinished
	}
	task.UpdatedAt = ctx.BlockTime().Unix()
	k.SetTask(ctx, task)

	// TB31: derive observation for reputation update
	// MVP thresholds (can be moved to params later)
	const (
		cpuThr    = uint64(5000)
		memThr    = uint64(800)
		netThr    = uint64(5000)
		latThr    = uint64(2000)
		timeoutThr = uint64(4000)
	)

	resourceAnomaly := msg.CpuMs > cpuThr || msg.MemMbPeak > memThr || msg.NetKb > netThr || msg.LatencyMs > latThr
	timeout := msg.LatencyMs > timeoutThr

	obs := 0
	if timeout {
		obs = 2
		edge.Timeout += 1
	} else if resourceAnomaly {
		obs = 1
		edge.Anomalies += 1
	}

	// counters (best-effort)
	if stage == "RESULT" {
		edge.OnTime += 1
		// correctness unknown here; keep as-is
	}

	k.UpdateReputation(ctx, &edge, obs, "log:"+stage)
	k.SetEdge(ctx, edge)

	return &types.MsgSubmitLogSummaryResponse{}, nil
}
