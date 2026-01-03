package types

import errorsmod "cosmossdk.io/errors"

// x/tbthree module sentinel errors
var (
	ErrInvalidRequest        = errorsmod.Register(ModuleName, 1, "invalid request")
	ErrNotAuthorized         = errorsmod.Register(ModuleName, 2, "not authorized")
	ErrEdgeAlreadyRegistered = errorsmod.Register(ModuleName, 3, "edge already registered")
	ErrEdgeNotFound          = errorsmod.Register(ModuleName, 4, "edge not found")
	ErrProposalNotFound      = errorsmod.Register(ModuleName, 5, "proposal not found")
	ErrProposalNotPending    = errorsmod.Register(ModuleName, 6, "proposal is not pending")
	ErrAdminNotSet           = errorsmod.Register(ModuleName, 7, "admin not set")

	// Ignite v29 generated handlers sometimes expect ErrInvalidSigner.
	// Keep it in module errors to avoid having to patch generated files.
	ErrInvalidSigner = errorsmod.Register(ModuleName, 8, "invalid signer")
)
