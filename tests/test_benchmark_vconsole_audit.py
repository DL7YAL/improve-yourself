import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
TOOLS = ROOT / "tools" / "benchmark"
AUDITOR = TOOLS / "audit_benchmark_vconsole.py"


def load_auditor():
    sys.path.insert(0, str(TOOLS))
    spec = importlib.util.spec_from_file_location("audit_benchmark_vconsole", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def vconsole_text(module, bot_count=10, extra_lines=()) -> str:
    runtime = sys.modules["validate_benchmark_runtime"]
    lines = [f"[   cs_script ]: [IYBENCH] {runtime.EXPECTED_EVENTS[0]}"]
    for index in range(bot_count):
        name = f"Bot{index}"
        lines.append(f"[ General ]: ClientPutInServer create new player controller [{name}]")
        lines.append(f'[ General ]: "{name}<{index + 1}><BOT><Unassigned>" ChangeTeam()')
    lines.extend(extra_lines)
    lines.extend(
        f"[   cs_script ]: [IYBENCH] {event}"
        for event in runtime.EXPECTED_EVENTS[1:]
    )
    return "\n".join(lines) + "\n"


def test_clean_complete_vconsole_is_clear() -> None:
    module = load_auditor()
    result = module.audit_text(vconsole_text(module), "abc")
    assert result["status"] == "CLEAR"
    assert result["runtime_contract_status"] == "PASS"
    assert result["observed_bots_at_first_warmup"] == 10
    assert result["diagnostics"] == []


def test_engine_and_bot_findings_keep_contract_pass_but_need_work() -> None:
    module = load_auditor()
    extra = (
        '[ W ResourceSystem ]: Failed loading resource "maps/improve_yourself_benchmark/'
        'cubemaps/env_cubemap_array.vtex_c" (ERROR_FILEOPEN: File not found)',
        "[ W Client ]: Unable to determine cubemap texture for env_cubemap_fog",
        "[ W InputService ]: Cannot execute concommand '+attack', missing required FCVAR flag",
    )
    result = module.audit_text(vconsole_text(module, bot_count=9, extra_lines=extra), "def")
    assert result["status"] == "NEEDS_WORK"
    assert result["runtime_contract_status"] == "PASS"
    assert result["observed_bots_at_first_warmup"] == 9
    assert {item["id"] for item in result["diagnostics"]} == {
        "cubemap_resource_missing",
        "cubemap_fog_unresolved",
        "required_client_command_denied",
        "bot_population_mismatch",
    }


def test_partial_contract_is_blocked_even_without_engine_messages() -> None:
    module = load_auditor()
    text = vconsole_text(module).split("PASS_END type=measured", 1)[0]
    result = module.audit_text(text, "123")
    assert result["status"] == "BLOCKED"
    assert result["runtime_contract_status"] == "PARTIAL"
