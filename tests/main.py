import sys
import pytest


def main():
    print("Running tests...")
    # Pass all command line arguments to pytest
    sys.exit(pytest.main(sys.argv[1:]))


if __name__ == "__main__":
    main()
