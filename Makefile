.PHONY: all test-rc-release test-direct-release clean

all: clean test-rc-release test-direct-release

# Test a valid release based on RC tag (should succeed)
test-rc-release:
	@echo "===== Testing release with RC tag ====="
	@./test_scripts/test_rc_release.sh
	@echo "✅ RC-based release test completed"

# Test a release without RC tag (should fail workflow)
test-direct-release:
	@echo "===== Testing direct release without RC tag ====="
	@./test_scripts/test_direct_release.sh || true
	@echo "✅ Direct release test completed (expected failure in GitHub Actions)"

# Run cleanup to reset repository state
clean:
	@echo "===== Cleaning up test artifacts ====="
	@./test_scripts/cleanup.sh
	@echo "✅ Cleanup completed"