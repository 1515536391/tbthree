package keeper

import (
	"context"
	"errors"

	sdk "github.com/cosmos/cosmos-sdk/types"

	"tbthree/x/tbthree/types"
)

// adminKey = AdminKeyPrefix || addrBytes
func adminKey(addr sdk.AccAddress) []byte {
	k := make([]byte, 0, len(types.AdminKeyPrefix)+len(addr))
	k = append(k, []byte(types.AdminKeyPrefix)...)
	k = append(k, addr.Bytes()...)
	return k
}

func (k Keeper) SetAdmin(ctx context.Context, addr sdk.AccAddress) error {
	store := k.storeService.OpenKVStore(ctx)
	return store.Set(adminKey(addr), []byte{1})
}

func (k Keeper) GetAdmin(ctx context.Context, addr sdk.AccAddress) (bool, error) {
	store := k.storeService.OpenKVStore(ctx)
	bz, err := store.Get(adminKey(addr))
	if err != nil {
		return false, err
	}
	return bz != nil, nil
}

func (k Keeper) IsAdmin(ctx context.Context, addr sdk.AccAddress) bool {
	ok, err := k.GetAdmin(ctx, addr)
	return err == nil && ok
}

func (k Keeper) EnsureAdmin(ctx context.Context, addr sdk.AccAddress) error {
	if k.IsAdmin(ctx, addr) {
		return nil
	}
	return errors.New("not admin")
}
