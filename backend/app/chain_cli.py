from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class TxResult:
    raw: dict[str, Any]

    @property
    def txhash(self) -> str | None:
        return self.raw.get("txhash") or self.raw.get("tx_hash")

    @property
    def height(self) -> int | None:
        h = self.raw.get("height")
        if h is None:
            return None
        try:
            return int(h)
        except Exception:
            return None


class ChainCLI:
    def __init__(
        self,
        *,
        tbthreed: str,
        chain_id: str,
        node: str,
        home: str,
        module: str = "tbthree",
        keyring_backend: str = "test",
    ) -> None:
        self.tbthreed = tbthreed
        self.chain_id = chain_id
        self.node = node
        self.home = home
        self.module = module
        self.keyring_backend = keyring_backend

    def _run(self, args: Sequence[str]) -> tuple[int, str, str]:
        p = subprocess.run(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    def _run_json(self, args: Sequence[str]) -> dict[str, Any]:
        code, out, err = self._run(args)
        if code != 0:
            raise RuntimeError(f"Command failed ({code}): {' '.join(args)}\n{err}\n{out}")
        if out == "":
            return {}
        try:
            return json.loads(out)
        except Exception as e:
            raise RuntimeError(f"Non-JSON output: {' '.join(args)}\n{out}") from e

    def keys_show_addr(self, name: str) -> str:
        code, out, err = self._run(
            [
                self.tbthreed,
                "keys",
                "show",
                name,
                "-a",
                "--keyring-backend",
                self.keyring_backend,
                "--home",
                self.home,
            ]
        )
        if code != 0:
            raise RuntimeError(err or out)
        return out

    def tx(self, module: str, cmd: str, args: Sequence[str], *, from_name: str) -> TxResult:
        base = [
            self.tbthreed,
            "tx",
            module,
            cmd,
            *args,
            "--from",
            from_name,
            "--keyring-backend",
            self.keyring_backend,
            "--home",
            self.home,
            "--chain-id",
            self.chain_id,
            "--node",
            self.node,
            "--broadcast-mode",
            "sync",
            "-y",
            "--output",
            "json",
        ]
        raw = self._run_json(base)
        return TxResult(raw=raw)

    def query(self, module: str, cmd: str, args: Sequence[str]) -> dict[str, Any]:
        """Run `tbthreed query ...`.

        Note: some newer `tbthreed` builds removed `--node` from `query`.
        To keep compatibility across versions, we try with `--node` first,
        and fall back to running without it if the flag is rejected.
        """

        base_common = [
            self.tbthreed,
            "query",
            module,
            cmd,
            *args,
            "--home",
            self.home,
            "--output",
            "json",
        ]

        # Prefer explicit node when supported.
        with_node = [
            self.tbthreed,
            "query",
            module,
            cmd,
            *args,
            "--node",
            self.node,
            "--home",
            self.home,
            "--output",
            "json",
        ]

        try:
            return self._run_json(with_node)
        except RuntimeError as e:
            msg = str(e)
            if "unknown flag: --node" in msg or "unknown shorthand flag" in msg:
                return self._run_json(base_common)
            raise

    def keys_sign(self, name: str, data_file: str) -> str:
        # returns signature JSON, but we just return raw stdout (string)
        code, out, err = self._run(
            [
                self.tbthreed,
                "keys",
                "sign",
                name,
                data_file,
                "--keyring-backend",
                self.keyring_backend,
                "--home",
                self.home,
                "--output",
                "json",
            ]
        )
        if code != 0:
            raise RuntimeError(err or out)
        try:
            j = json.loads(out)
            return j.get("signature") or out
        except Exception:
            return out

    def keys_verify(self, address_or_name: str, signature: str, data_file: str) -> bool:
        code, out, err = self._run(
            [
                self.tbthreed,
                "keys",
                "verify",
                address_or_name,
                signature,
                data_file,
                "--keyring-backend",
                self.keyring_backend,
                "--home",
                self.home,
            ]
        )
        if code != 0:
            # some versions output nonzero on failure, treat as false
            return False
        # output contains "true" or "false"
        return "true" in out.lower()
