package keeper

import (
	"context"
	"time"

	errorsmod "cosmossdk.io/errors"
	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"

	"tbthree/x/tbthree/types"
)

func (k msgServer) ApproveProposal(goCtx context.Context, msg *types.MsgApproveProposal) (*types.MsgApproveProposalResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	// signer validation
	if _, err := sdk.AccAddressFromBech32(msg.Creator); err != nil {
		return nil, errorsmod.Wrap(sdkerrors.ErrInvalidAddress, err.Error())
	}

	admin, ok := k.GetAdmin(ctx)
	if !ok || admin == "" {
		return nil, errorsmod.Wrap(types.ErrNotAuthorized, "admin not set")
	}
	if msg.Creator != admin {
		return nil, errorsmod.Wrap(types.ErrNotAuthorized, "only admin can approve proposal")
	}

	proposal, found := k.GetGovernanceProposal(ctx, msg.ProposalId)
	if !found {
		return nil, errorsmod.Wrap(types.ErrProposalNotFound, msg.ProposalId)
	}
	if proposal.Status != types.ProposalStatusPending {
		return nil, errorsmod.Wrap(types.ErrProposalNotPending, proposal.Status)
	}

	now := time.Now().Unix()
	proposal.Status = types.ProposalStatusApproved
	proposal.ApprovedBy = admin
	proposal.DecidedAt = now
	k.SetGovernanceProposal(ctx, proposal)

	// best-effort: clear edge pending id (if it matches)
	if proposal.EdgeAddr != "" {
		ed, ok := k.GetEdge(ctx, proposal.EdgeAddr)
		if ok && ed.PendingProposalId == proposal.ProposalId {
			ed.PendingProposalId = ""
			ed.Status = types.EdgeStatusActive
			ed.UpdatedAt = now
			k.SetEdge(ctx, ed)
		}
	}

	return &types.MsgApproveProposalResponse{}, nil
}
