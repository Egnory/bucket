import json
import urllib.request
from pathlib import Path

SOURCE = (
    "https://raw.githubusercontent.com/"
    "ScoopInstaller/Main/master/bucket/7zip.json"
)

OUTPUT = Path("bucket/7zip.json")

PATCH = r"""
$langFile = Join-Path $dir 'Lang\zh-cn.txt'

if (-not (Test-Path $langFile)) {
    throw "Missing language file: $langFile"
}

$content = [IO.File]::ReadAllText($langFile, [Text.Encoding]::UTF8)

$replacements = @{
    '解压到 {0}' = '解压到 {0}(&E)'
    '添加到 {0}' = '添加到 {0}(&Z)'
}

foreach ($old in $replacements.Keys) {
    $new = $replacements[$old]

    if ($content.Contains($old)) {
        $content = $content.Replace($old, $new)
    }
    elseif (-not $content.Contains($new)) {
        throw "Cannot find language entry: $old"
    }
}

[IO.File]::WriteAllText(
    $langFile,
    $content,
    [Text.UTF8Encoding]::new($false)
)
""".strip().splitlines()

def main():
    request = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "Egnory-Scoop-Bucket"}
    )

    with urllib.request.urlopen(request) as response:
        manifest = json.load(response)

    if not isinstance(manifest.get("post_install"), list):
        raise RuntimeError("Unexpected upstream post_install format")

    # 防止重复注入
    marker = "$langFile = Join-Path $dir 'Lang\\zh-cn.txt'"

    manifest["post_install"] = [
        line for line in manifest["post_install"]
        if line.strip() != marker
    ]

    manifest["post_install"].extend(PATCH)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )

    print(f"Updated {OUTPUT}")
    print(f"Upstream version: {manifest['version']}")

if __name__ == "__main__":
    main()
