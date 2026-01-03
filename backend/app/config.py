from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    # Chain / CLI
    chain_name: str
    module_name: str
    chain_id: str
    chain_rpc: str
    chain_home: str
    tbthreed: str
    keyring_backend: str
    denom: str

    # Actors
    admin_name: str
    admin_addr: str
    cloud_name: str
    cloud_addr: str
    vehicle1_name: str
    vehicle1_addr: str
    edge1_name: str
    edge1_addr: str
    edge2_name: str
    edge2_addr: str
    edge3_name: str
    edge3_addr: str

    # Storage
    db_url: str


def _first_env(*keys: str, default: str | None = None) -> str | None:
    """Return the first non-empty env value in keys."""
    for k in keys:
        v = os.getenv(k)
        if v is not None and v.strip() != "":
            return v.strip()
    return default


def _default_chain_home(chain_name: str, chain_id: str) -> str:
    # Ignite/Cosmos defaults to ~/.<chain_name>
    home = Path.home() / f".{chain_name}"
    if home.exists():
        return str(home)
    # fallback: ~/.<chain_id>
    alt = Path.home() / f".{chain_id}"
    return str(alt)


def _default_tbthreed() -> str:
    return (
        _first_env("TBTHREED", "TB3D")
        or shutil.which("tbthreed")
        or shutil.which("tb3d")
        or "tbthreed"
    )


def _resolve_addrs(
    *,
    tbthreed: str,
    chain_id: str,
    chain_rpc: str,
    chain_home: str,
    module_name: str,
    keyring_backend: str,
    names_and_addrs: list[tuple[str, str]],
) -> dict[str, str]:
    """Resolve missing addresses from local keyring via `tbthreed keys show <name> -a`."""
    try:
        from .chain_cli import ChainCLI

        cli = ChainCLI(
            tbthreed=tbthreed,
            chain_id=chain_id,
            node=chain_rpc,
            home=chain_home,
            module=module_name,
            keyring_backend=keyring_backend,
        )

        resolved: dict[str, str] = {}
        for name, addr in names_and_addrs:
            if addr and addr.strip() != "":
                resolved[name] = addr.strip()
                continue
            got = cli.keys_show_addr(name)
            resolved[name] = got.strip() if got else ""
        return resolved
    except Exception:
        # If anything goes wrong (missing binary, etc.), do not crash startup.
        return {name: (addr.strip() if addr else "") for name, addr in names_and_addrs}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Load backend/.env if present
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Defaults tuned for tbthree (Ignite v29 flow)
    chain_name = _first_env("CHAIN_NAME", default="tbthree") or "tbthree"
    chain_id = _first_env("CHAIN_ID", default=chain_name) or chain_name
    module_name = _first_env("MODULE_NAME", default=chain_name) or chain_name

    chain_rpc = _first_env(
        "CHAIN_RPC",
        "RPC_URL",  # common user-provided name
        default="tcp://127.0.0.1:26657",
    ) or "tcp://127.0.0.1:26657"

    chain_home = _first_env("CHAIN_HOME", default=_default_chain_home(chain_name, chain_id)) or _default_chain_home(
        chain_name, chain_id
    )

    tbthreed = _default_tbthreed()
    keyring_backend = _first_env("KEYRING_BACKEND", default="test") or "test"
    denom = _first_env("DENOM", default="utoken") or "utoken"

    admin_name = _first_env("ADMIN_NAME", default="alice") or "alice"
    cloud_name = _first_env("CLOUD_NAME", default="cloud1") or "cloud1"
    vehicle1_name = _first_env("VEHICLE1_NAME", default="vehicle1") or "vehicle1"
    edge1_name = _first_env("EDGE1_NAME", default="edge1") or "edge1"
    edge2_name = _first_env("EDGE2_NAME", default="edge2") or "edge2"
    edge3_name = _first_env("EDGE3_NAME", default="edge3") or "edge3"

    # Addresses are OPTIONAL in env; we will try to derive from keyring.
    admin_addr_env = _first_env("ADMIN_ADDR", default="") or ""
    cloud_addr_env = _first_env("CLOUD_ADDR", default="") or ""
    vehicle1_addr_env = _first_env("VEHICLE1_ADDR", default="") or ""
    edge1_addr_env = _first_env("EDGE1_ADDR", default="") or ""
    edge2_addr_env = _first_env("EDGE2_ADDR", default="") or ""
    edge3_addr_env = _first_env("EDGE3_ADDR", default="") or ""

    resolved = _resolve_addrs(
        tbthreed=tbthreed,
        chain_id=chain_id,
        chain_rpc=chain_rpc,
        chain_home=chain_home,
        module_name=module_name,
        keyring_backend=keyring_backend,
        names_and_addrs=[
            (admin_name, admin_addr_env),
            (cloud_name, cloud_addr_env),
            (vehicle1_name, vehicle1_addr_env),
            (edge1_name, edge1_addr_env),
            (edge2_name, edge2_addr_env),
            (edge3_name, edge3_addr_env),
        ],
    )

    # DB
    db_path = Path(__file__).resolve().parents[1] / "data" / "tbthree.db"
    db_url = os.getenv("DB_URL") or f"sqlite:///{db_path}"

    return Settings(
        chain_name=chain_name,
        module_name=module_name,
        chain_id=chain_id,
        chain_rpc=chain_rpc,
        chain_home=chain_home,
        tbthreed=tbthreed,
        keyring_backend=keyring_backend,
        denom=denom,
        admin_name=admin_name,
        admin_addr=resolved.get(admin_name, admin_addr_env),
        cloud_name=cloud_name,
        cloud_addr=resolved.get(cloud_name, cloud_addr_env),
        vehicle1_name=vehicle1_name,
        vehicle1_addr=resolved.get(vehicle1_name, vehicle1_addr_env),
        edge1_name=edge1_name,
        edge1_addr=resolved.get(edge1_name, edge1_addr_env),
        edge2_name=edge2_name,
        edge2_addr=resolved.get(edge2_name, edge2_addr_env),
        edge3_name=edge3_name,
        edge3_addr=resolved.get(edge3_name, edge3_addr_env),
        db_url=db_url,
    )
