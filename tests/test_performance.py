"""Performance tests for jsonfix."""

from __future__ import annotations

import time

import pytest

from jsonfix import loads_relaxed


class TestPerformance:
    """Ensure acceptable performance on large inputs."""

    @pytest.mark.slow
    def test_large_array_performance(self) -> None:
        """Should handle 100k element array in under 5 seconds."""
        large_json = "[" + ",".join(["1"] * 100000) + "]"
        start = time.time()
        result = loads_relaxed(large_json)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Took {elapsed:.2f}s, expected < 5.0s"
        assert len(result) == 100000

    @pytest.mark.slow
    def test_large_object_performance(self) -> None:
        """Should handle 10k key object in under 3 seconds."""
        pairs = [f'"key{i}": {i}' for i in range(10000)]
        large_json = "{" + ", ".join(pairs) + "}"
        start = time.time()
        result = loads_relaxed(large_json)
        elapsed = time.time() - start
        assert elapsed < 3.0, f"Took {elapsed:.2f}s, expected < 3.0s"
        assert len(result) == 10000

    @pytest.mark.slow
    def test_deeply_nested_performance(self) -> None:
        """Should handle 100 levels of nesting."""
        nested = '{"a":' * 100 + "1" + "}" * 100
        start = time.time()
        result = loads_relaxed(nested)
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Took {elapsed:.2f}s, expected < 1.0s"
        # Verify structure
        current = result
        for _ in range(100):
            assert "a" in current
            current = current["a"]
        assert current == 1

    @pytest.mark.slow
    def test_large_string_performance(self) -> None:
        """Should handle 1MB string value in under 12 seconds."""
        large_string = "x" * (1024 * 1024)  # 1MB
        large_json = f'{{"text": "{large_string}"}}'
        start = time.time()
        result = loads_relaxed(large_json)
        elapsed = time.time() - start
        assert elapsed < 12.0, f"Took {elapsed:.2f}s, expected < 12.0s"
        assert len(result["text"]) == 1024 * 1024

    @pytest.mark.slow
    def test_many_repairs_performance(self) -> None:
        """Should handle many repairs efficiently."""
        # 1000 trailing commas
        items = [f'{{"k{i}": {i},}}' for i in range(1000)]
        large_json = "[" + ", ".join(items) + "]"

        repairs: list = []
        start = time.time()
        result = loads_relaxed(large_json, repair_log=repairs)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Took {elapsed:.2f}s, expected < 3.0s"
        assert len(result) == 1000
        assert len(repairs) >= 1000  # At least 1000 trailing comma repairs


class TestPerformanceWithRelaxations:
    """Test performance with various relaxations enabled."""

    @pytest.mark.slow
    def test_single_quotes_large_array(self) -> None:
        """Single-quote conversion on large array."""
        items = ["'item'" for _ in range(10000)]
        large_json = "[" + ", ".join(items) + "]"

        start = time.time()
        result = loads_relaxed(large_json)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Took {elapsed:.2f}s, expected < 3.0s"
        assert len(result) == 10000

    @pytest.mark.slow
    def test_comments_large_file(self) -> None:
        """Comment stripping on large file with many comments."""
        lines = []
        for i in range(1000):
            lines.append(f"// Comment {i}")
            lines.append(f'  "key{i}": {i},')
        content = "{\n" + "\n".join(lines[:-1]) + "\n" + lines[-1].rstrip(",") + "\n}"

        start = time.time()
        result = loads_relaxed(content)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Took {elapsed:.2f}s, expected < 3.0s"
        assert len(result) == 1000
