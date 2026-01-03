TB3 backend fixpack K

Changes:
1) Fix NameError: import timezone (used in demo_seed/create_task timestamps)
2) Make ChainCLI.query compatible with tbthreed versions that removed `--node`.
   - Try with --node first; if rejected (unknown flag), retry without.

Apply:
- From project root (the directory that contains backend/ frontend/ chain/):
    tar -xzf <this_file>.tgz --touch
- Restart backend.
