# FPGA project

The active project is [enigma/enigma.ffpga](enigma/enigma.ffpga), targeting SLG47910V Rev BB in Go Configure 6.55.002. `enigma_shrike/` contains historical scaffolding and is not the active build.

Regenerate `enigma/ffpga/src/main.v` from `fpga/rtl` using `python3 tools/prepare_fpga.py` at the repository root. Physical I/O assignments are in the project and `enigma/pins.csv`; timing constraints are in `enigma/ffpga/timing-constraints/clocks.sdc`.

Read [the build guide](../../docs/BUILD_AND_USE.md) for generation and image formats and [STATUS.md](../../STATUS.md) for acceptance evidence. The divided clock must use the explicit, enabled internal LaC1 feedback path. The previous implicit logic clock mapped to an unconnected input.
