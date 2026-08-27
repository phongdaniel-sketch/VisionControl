import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--controller":
        from vision_control.app import main as controller_main
        controller_main(sys.argv[2:])
        return 0
    from vision_control.settings_ui import main as settings_main
    return settings_main()


if __name__ == "__main__":
    raise SystemExit(main())
