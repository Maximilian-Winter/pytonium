import importlib.util
from pathlib import Path


PREPARE_BUILD_PATH = Path(__file__).with_name("prepare_build.py")


def _load_prepare_build_module():
    spec = importlib.util.spec_from_file_location("prepare_build", PREPARE_BUILD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_windows_runtime_copy_includes_cef_data_files(tmp_path, monkeypatch):
    prepare_build = _load_prepare_build_module()
    cef_root = tmp_path / "cef"
    release_dir = cef_root / "Release"
    resources_dir = cef_root / "Resources"
    release_dir.mkdir(parents=True)
    resources_dir.mkdir()

    runtime_files = {
        "libcef.dll": b"dll",
        "bootstrap.exe": b"exe",
        "v8_context_snapshot.bin": b"snapshot",
        "vk_swiftshader_icd.json": b"json",
    }
    for name, contents in runtime_files.items():
        (release_dir / name).write_bytes(contents)

    framework_dir = tmp_path / "framework"
    monkeypatch.setattr(prepare_build, "CEF_BINARIES_WINDOWS", cef_root)
    monkeypatch.setattr(prepare_build, "PYTHON_FRAMEWORK_DIR", framework_dir)

    assert prepare_build.copy_cef_runtime("windows") == 1

    output_dir = framework_dir / "Pytonium" / "bin_win"
    for name, contents in runtime_files.items():
        assert (output_dir / name).read_bytes() == contents
