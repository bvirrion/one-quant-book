import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import gen_wirecodec as g  # noqa: E402


def test_generated_files_are_current():
    assert g.main(["--check"]) == 0


def test_sbe_schema_is_little_endian_and_covers_every_feed_message():
    import xml.etree.ElementTree as ET
    root = ET.fromstring((HERE / "sbe/feed_sbe.xml").read_text())
    assert root.get("byteOrder") == "littleEndian"
    ns = {"sbe": "http://fixprotocol.io/2016/sbe"}
    names = {m.get("name") for m in root.findall("sbe:message", ns)}
    assert names == {f"Feed{t}" for t in g.schema()["protocols"]["feed"]}
    a = next(m for m in root.findall("sbe:message", ns) if m.get("name") == "FeedA")
    assert a.get("blockLength") == "37"          # 35 bytes of fields on the wire, the 48-bit timestamp widened to 64


def test_the_generator_is_deterministic():
    first = g.outputs()
    assert first == g.outputs()
    out = subprocess.run([sys.executable, str(HERE / "gen_wirecodec.py"), "--check"], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout
