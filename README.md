# pipewire-latency

Small CLI to inspect and tune PipeWire buffer latency on Linux. It reads the active graph quantum and sample rate, reports buffer latency, and writes a drop-in config for a chosen profile.

It does not require root, does not run a daemon, and does not replace `pw-top` or a real round-trip latency measurement. It reports graph buffer latency from quantum and sample rate.

## Install

```bash
git clone https://github.com/negg0s/pipewire-latency.git
cd pipewire-latency
python -m pip install --user .
```

Or run it without installing:

```bash
python -m pip install --user -e .
pipewire-latency --help
```

## Usage

```bash
# Show the active quantum, sample rate, driver, and buffer latency
pipewire-latency info

# Print only the buffer latency
pipewire-latency measure

# Machine readable output
pipewire-latency measure --json

# Preview a config without writing it
pipewire-latency tune --profile gaming --dry-run

# Write the drop-in, then restart the user services
pipewire-latency tune --profile gaming
systemctl --user restart pipewire pipewire-pulse wireplumber

# Roll back to the newest backup, or remove the file if no backup exists
pipewire-latency restore

# Markdown report for a bug report or a forum post
pipewire-latency report --profile gaming

# Check commands and state
pipewire-latency doctor
```

## Profiles

| Profile | Quantum | Rate | Buffer |
| --- | ---: | ---: | ---: |
| `safe` | 1024 | 48000 | 21.33 ms |
| `balanced` | 256 | 48000 | 5.33 ms |
| `gaming` | 64 | 48000 | 1.33 ms |
| `music` | 128 | 48000 | 2.67 ms |
| `pro-audio` | 32 | 48000 | 0.67 ms |

Lower quantum means lower latency and a higher chance of xruns. Start with `balanced`, then move one step down only if `pw-top` stays clean.

## Config path

By default the tool writes:

```text
~/.config/pipewire/pipewire.conf.d/99-pipewire-latency.conf
```

Override it with `--config` or `PIPEWIRE_LATENCY_CONFIG`.

The file uses `default.clock.quantum`, `default.clock.min-quantum`, and `default.clock.max-quantum`. It does not touch system-wide config under `/etc`.

## What it does not do

- It does not measure round-trip latency. Use a loopback interface and a tool such as `jack_iodelay` for that.
- It does not tune USB, Bluetooth, or HDMI-specific quirks.
- It does not restart PipeWire for you. It prints the command.
- It does not claim that a lower quantum is always better. A stable graph beats a low number.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## License

MIT. See `LICENSE`.
