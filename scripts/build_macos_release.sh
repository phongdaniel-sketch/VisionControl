#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
app_path="$repo_dir/dist/VisionControl.app"
zip_path="$repo_dir/dist/VisionControl-0.1.0-macOS-arm64.zip"
dmg_path="$repo_dir/dist/VisionControl-0.1.0-macOS-arm64.dmg"
notarize=false
skip_build=false

usage() {
  echo "Usage: $0 [--skip-build] [--notarize]"
  echo "  VISIONCONTROL_SIGN_IDENTITY: Developer ID Application identity"
  echo "  VISIONCONTROL_NOTARY_PROFILE: notarytool Keychain profile"
}

while (($#)); do
  case "$1" in
    --skip-build) skip_build=true ;;
    --notarize) notarize=true ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

cd "$repo_dir"

sign_identity="${VISIONCONTROL_SIGN_IDENTITY:-}"
if [[ -n "$sign_identity" ]]; then
  if [[ "$sign_identity" != Developer\ ID\ Application:* ]]; then
    echo "Release signing requires a Developer ID Application identity." >&2
    exit 1
  fi
  if ! security find-identity -v -p codesigning | grep -Fq "\"$sign_identity\""; then
    echo "Signing identity is not available in the current Keychain: $sign_identity" >&2
    exit 1
  fi
fi

if [[ "$skip_build" == false ]]; then
  .venv311/bin/pyinstaller --noconfirm --clean VisionControl.spec
fi

if [[ ! -d "$app_path" ]]; then
  echo "Missing application bundle: $app_path" >&2
  exit 1
fi

codesign --verify --deep --strict "$app_path"
plutil -extract NSCameraUsageDescription raw "$app_path/Contents/Info.plist" >/dev/null

if [[ "$notarize" == true ]]; then
  if [[ -z "$sign_identity" ]]; then
    echo "--notarize requires VISIONCONTROL_SIGN_IDENTITY." >&2
    exit 1
  fi
  notary_profile="${VISIONCONTROL_NOTARY_PROFILE:-}"
  if [[ -z "$notary_profile" ]]; then
    echo "--notarize requires VISIONCONTROL_NOTARY_PROFILE." >&2
    exit 1
  fi

  notary_zip="$repo_dir/dist/VisionControl-notarization.zip"
  rm -f "$notary_zip"
  ditto -c -k --sequesterRsrc --keepParent "$app_path" "$notary_zip"
  xcrun notarytool submit "$notary_zip" --keychain-profile "$notary_profile" --wait
  xcrun stapler staple "$app_path"
  xcrun stapler validate "$app_path"
  rm -f "$notary_zip"
fi

# hdiutil can reject a source bundle located on a removable/external volume.
# Stage and validate both artifacts locally, then replace the published copies
# only after both succeed.
stage_root="$(mktemp -d "${TMPDIR:-/tmp}/VisionControl-release.XXXXXX")"
cleanup() {
  rm -rf "$stage_root"
}
trap cleanup EXIT
mkdir "$stage_root/payload"
ditto -c -k --sequesterRsrc --keepParent "$app_path" \
  "$stage_root/VisionControl.zip"
ditto "$app_path" "$stage_root/payload/VisionControl.app"
hdiutil create -volname VisionControl -srcfolder "$stage_root/payload" \
  -ov -format UDZO "$stage_root/VisionControl.dmg"

codesign --verify --deep --strict "$app_path"
unzip -tq "$stage_root/VisionControl.zip"
hdiutil verify "$stage_root/VisionControl.dmg"
cp "$stage_root/VisionControl.zip" "$zip_path"
cp "$stage_root/VisionControl.dmg" "$dmg_path"
shasum -a 256 "$zip_path" "$dmg_path"
du -sh "$app_path" "$zip_path" "$dmg_path"
