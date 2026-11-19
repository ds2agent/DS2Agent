# QEMU and simulation backends

QEMU is an optional firmware-execution backend, not a prerequisite for datasheet conversion.
Use a host-compiled driver harness first. A C transfer-function evaluator is not a bus device
emulator, and neither a C mock nor a datasheet can be loaded directly as a QEMU peripheral.

## Select the verification scope

| Backend | Executes | Establishes only |
|---|---|---|
| `model` | register/command operations against a deterministic state model | supported model semantics |
| `native` | the actual exported C driver against a fake HAL and host device model | compiled driver behavior at the HAL boundary |
| `qemu` | a firmware image on a verified QEMU machine/peripheral configuration | firmware behavior within that configuration's modeled scope |

For a selected portable C driver, `native` is the baseline verification path. Compile the
exported `.c` and `.h` unchanged; keep `main`, test assertions, fake HAL and device model in
a separate harness. Exercise initialization, configuration, read/interpret, and documented
failure paths relevant to the selected operations. A Python tool passing against an
in-memory register dictionary does not verify the C driver.

Model the documented writes, reset, reply layout, state transitions and virtual-time delays
needed by each scenario. Unmodeled operations must fail explicitly rather than return a
plausible default. Expected results come from cited reference vectors or an independent
derivation, not just agreement between driver and mock generated from the same formula.

## Generated `run_sim` contract

Require an explicit `backend` and validate mutually exclusive request shapes:

| Backend | Other required arguments |
|---|---|
| `model` | `operations`: ordered register/command operations |
| `native` | `scenario_id`: a project-owned driver-harness scenario |
| `qemu` | `scenario_id`, `firmware_id`, `target_id`: project-owned scenario, firmware and target records |

Advertise only implemented backends. An unsupported backend/target/scenario returns
`status: unsupported` and a reason without launching a process. Never fall back from QEMU
to native or model execution, or count a compile-only check as an executed scenario.

Every result includes:

- `backend`, `status` (`passed`, `failed`, `unsupported`), `physical: false`;
- `trace`, `checks` (expected/actual outcomes with source bindings), `artifacts` (relative
  paths and content hashes), and `limitations`;
- for `model`, `final_state` and `error_code`;
- for `native`/`qemu`, exact build/run argument vectors and tool versions, driver/HAL/model/
  harness hashes, stdout/stderr paths, process exit status and timeout outcome;
- for `qemu`, firmware hash/ID, target ID, machine, CPU, and modeled/missing peripherals.

Use `reason` for unsupported results; fields for work not executed are empty or explicitly
not run, never fabricated. A timeout, crash, or failed assertion is `failed`. Process exit
zero or an empty assertion list is insufficient for `passed`. Retain detailed run evidence
under `reports/simulation/`; ship runtime harnesses, models and build recipes needed by a
delivered backend, not scratch logs.

## QEMU target admission

Before advertising a target, record and verify:

1. The QEMU executable/build and version; available machine/device inventory
   (`qemu-system-arm -machine help`, `qemu-system-arm -device help` for ARM).
2. Exact machine and its supported CPU, memory map, firmware format, load address and
   boot method; compiler/linker options and startup code must match that machine.
3. Every exercised peripheral, including interrupt routing and any required modeled clock,
   timer, UART, I2C/SPI controller and external device connection.
4. A finite boot/run scenario with independently checked observable results, its exact
   command arguments, firmware hash, output trace, deadline and known omissions.

A physical NUCLEO-F103/G071/F767 board profile does not establish QEMU support. Sharing a
Cortex-M family is insufficient; overriding `-cpu` does not add missing MCU peripherals.
Do not provide a generic `-machine <board> -cpu cortex-m4` recipe as a tested target.
No QEMU target is certified by this skill's board profiles alone.

`-device` instantiates device types supported by the selected QEMU build; it does not load
arbitrary C mocks. A new sensor model requires QEMU device/bus integration and a build that
includes it, followed by independent protocol/state checks. Do not generate such a port
implicitly to fill missing target support. For writing and wiring such a model, follow
[qemu-device-model.md](qemu-device-model.md).

If a driver uses a fake HAL inside QEMU, label the scope **driver on target CPU**, not MCU
I2C/SPI integration. CPU/startup-only execution likewise cannot establish sensor support.
Unsupported required peripherals block that integration scope; retain any narrower
successful evidence with its actual scope, not a substituted success.

### Version-aware support checklist

Use the documentation shipped for the selected release/build, plus its actual machine
inventory; the upstream `master` manual is a discovery reference, not proof that an
installed release implements an option. Inventory commands above are admission templates,
not commands exercised by this guide. Record machine properties, accelerator choice,
QEMU source/package revision and any patches/device models with hashes. A device listed
by `-device help` may still be impossible to attach to the selected machine's buses.

For each required feature, keep a small matrix: firmware operation, MCU controller,
external device model, bus/address or chip-select connection, IRQ/clock dependency,
source for claimed support, and observed check. Inspect board-specific omissions and,
where the documentation is insufficient, the selected QEMU source. An acknowledged
unimplemented-register access is not proof of working hardware integration. Missing
DMA, reset semantics, timeouts or interrupts can invalidate a polling-only success for
the requested scope.

Re-admit affected scenarios after changing QEMU, firmware startup/linker layout, HAL,
machine properties or peripheral models. Keep a physical board target and a QEMU
machine record distinct, even if they share some driver sources.

## Observability and finite completion

Choose an observation path implemented by the exact machine and firmware:

- Capture the intended modeled UART with a dedicated character backend. `-display none`
  disables graphics, not all serial/monitor handling; `-nographic` can multiplex serial
  and monitor traffic. Separate machine-readable scenario output from monitor chatter.
- A scenario should emit its identity, checked results and an unambiguous completion
  marker, or expose an equivalent debugger-visible result. Require a nonempty expected
  check set and reject stale output from another image/scenario.
- For diagnosis, `-S` stops CPUs at startup and `-gdb` enables a debugger endpoint.
  Configure a local-only endpoint explicitly, avoid port collisions, and bound debugger
  waits. A paused guest is not a boot failure until the scenario's intended run begins.
- QEMU `-d`/`-D` logging and trace events are build/version-dependent. Select only
  available events, cap retained log size and correlate them with the driver/HAL trace.
  Repeated resets, fault loops and unimplemented accesses need explanation, not masking.
- Semihosting requires compatible guest calls/runtime and explicit opt-in. It exposes
  host interactions and is not a substitute for a modeled UART or physical I/O. Do not
  enable it implicitly to make a build appear functional.

Define the guest completion protocol and host wall-clock deadline independently of
virtual time. A microcontroller's normal infinite main loop will not make QEMU exit
automatically. On deadline terminate and reap the owned process, retain partial logs,
and report timeout as failed; never interpret killing QEMU as successful guest exit.
Do not launch an unowned background emulator or an unrestricted debugger service.

## Execution and evidence boundaries

Building/executing generated C or launching QEMU requires explicit `--allow-code-execution`
or the host equivalent. Never auto-install compilers, SDKs, firmware or QEMU. Resolve owned
scenario/firmware/target IDs to validated artifacts; use argument vectors, not caller-supplied
shell commands, and impose finite build/run deadlines. QEMU is not a security sandbox.

QEMU is functional, not cycle-accurate. None of these simulation backends proves electrical
compatibility, physical bus timing, sensor accuracy or board calibration. Simulation output
never becomes a physical observation. Report source, model, native, QEMU and hardware
verification separately; unavailable requested hardware work remains blocked, while
source/simulation delivery can proceed with explicit limits.

## Primary references

- [QEMU Arm system emulation and board selection](https://www.qemu.org/docs/master/system/target-arm.html):
  CPU compatibility is not machine/peripheral compatibility.
- [QEMU invocation reference](https://www.qemu.org/docs/master/system/invocation.html):
  machine inventory, character backends, debugger, tracing and semihosting options.
- [GCC native/target build requirements](gcc.md); physical programming remains a separate
  authorized workflow through [OpenOCD](openocd.md) or a selected vendor tool.
