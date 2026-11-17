# Runnable examples and synthetic output

- [Gmail](gmail-workflows/README.md), [Calendar](calendar-workflows/README.md) and [Drive](drive-workflows/README.md) prompts use the existing canonical tools.
- [Document generation](document-generation/README.md) contains four real baseline files with checksum/readback metadata.
- [Multi-server workflows](multi-server-workflows/README.md) contains the independent official client and captured Northstar trace.

Start `make dev` and choose Explore demo. These examples use synthetic data; the curated FakeLLM is not general reasoning. Google writes still require exact approval in mock mode. Baseline captures are preserved separately from fresh migration verification.
