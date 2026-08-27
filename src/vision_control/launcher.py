import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--settings":
        from vision_control.settings_ui import main as settings_main
        return settings_main()
    if len(sys.argv) > 1 and sys.argv[1] == "--legacy-controller":
        from vision_control.app import main as controller_main
        controller_main(sys.argv[2:])
        return 0
    from vision_control.controller_ui import main as controller_main
    args = sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == "--controller" else sys.argv[1:]
    return controller_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
