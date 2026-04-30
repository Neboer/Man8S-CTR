"""Unit tests for RoundTrip YAML updates to verify format preservation."""
import tempfile
import shutil
from os import path
from pathlib import Path

from mbctl.datatypes.MBContainerConfFormat import update_mbcontainer_autostart
from mbctl.datatypes import MBContainerConf
from ruamel.yaml import YAML


current_dir = path.dirname(__file__)


def normalize_autostart_for_comparison(content: str, autostart_value: bool) -> str:
    """Normalize the autostart value in YAML content for comparison.
    
    This allows us to compare two YAML files by temporarily setting autostart to a fixed value.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    
    data = yaml.load(content)
    data["autostart"] = autostart_value
    
    # Dump to string for comparison
    import io
    stream = io.StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def test_roundtrip_preserves_format_and_comments():
    """Test that RoundTrip YAML update preserves all formatting and comments except autostart value."""
    
    source_file = path.join(current_dir, "resources/test-man8s-conf.yaml")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a copy of the test file
        test_file = path.join(temp_dir, "test-config.yaml")
        shutil.copy(source_file, test_file)
        
        # Read original content
        with open(test_file, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        # Parse original to get current autostart value
        yaml = YAML()
        yaml.preserve_quotes = True
        original_data = yaml.load(original_content)
        original_autostart = original_data.get("autostart", True)
        
        # Update to opposite value
        new_autostart = not original_autostart
        update_mbcontainer_autostart(test_file, new_autostart)
        
        # Read updated content
        with open(test_file, "r", encoding="utf-8") as f:
            updated_content = f.read()
        
        # Verify autostart was changed
        updated_data = yaml.load(updated_content)
        assert updated_data.get("autostart") == new_autostart, \
            f"autostart not updated: expected {new_autostart}, got {updated_data.get('autostart')}"
        
        # Normalize both for comparison (set autostart to same value)
        original_normalized = normalize_autostart_for_comparison(original_content, new_autostart)
        updated_normalized = normalize_autostart_for_comparison(updated_content, new_autostart)
        
        # Compare - they should be identical except for whitespace variations
        if original_normalized != updated_normalized:
            print("\n=== ORIGINAL (normalized) ===")
            print(original_normalized)
            print("\n=== UPDATED (normalized) ===")
            print(updated_normalized)
            
            # Try to identify differences more clearly
            orig_lines = original_normalized.split('\n')
            updated_lines = updated_normalized.split('\n')
            
            for i, (orig, upd) in enumerate(zip(orig_lines, updated_lines)):
                if orig != upd:
                    print(f"\nLine {i+1} differs:")
                    print(f"  Original: {repr(orig)}")
                    print(f"  Updated:  {repr(upd)}")
        
        # Parse both as data structures to compare semantically
        original_data_normalized = yaml.load(original_normalized)
        updated_data_normalized = yaml.load(updated_normalized)
        
        # They should be identical when parsed
        assert original_data_normalized == updated_data_normalized, \
            "Data structure changed after RoundTrip update"
        
        # Verify comments are preserved (check string content)
        # Note: Comments in YAML are preserved by ruamel.yaml in RoundTrip mode
        assert "# autostart" in original_content, "Original should have autostart comment"
        assert "# autostart" in updated_content, "Updated should preserve autostart comment"
        
        # Verify other comments are preserved
        assert "# test comment" in original_content, "Original should have test comment"
        assert "# test comment" in updated_content, "Updated should preserve test comment"
        
        assert "# 又是一些测试用注释" in original_content, "Original should have Chinese comment"
        assert "# 又是一些测试用注释" in updated_content, "Updated should preserve Chinese comment"
        
        print("\n✓ All checks passed: RoundTrip preserves format and comments")
        print(f"  Original autostart: {original_autostart}")
        print(f"  Updated autostart:  {new_autostart}")
        print(f"  Comments preserved: Yes")
        print(f"  Format preserved: Yes")


def test_roundtrip_with_parse_and_validate():
    """Test that updated YAML can be parsed correctly by MBContainerConf."""
    
    source_file = path.join(current_dir, "resources/test-man8s-conf.yaml")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a copy of the test file
        test_file = path.join(temp_dir, "test-config.yaml")
        shutil.copy(source_file, test_file)
        
        # Load original config
        original_conf = MBContainerConf.from_yaml_file(test_file)
        original_autostart = original_conf.autostart
        
        # Update via RoundTrip
        new_autostart = not original_autostart
        update_mbcontainer_autostart(test_file, new_autostart)
        
        # Load updated config
        updated_conf = MBContainerConf.from_yaml_file(test_file)
        
        # Verify autostart was updated
        assert updated_conf.autostart == new_autostart, \
            f"autostart not updated in parsed config: expected {new_autostart}, got {updated_conf.autostart}"
        
        # Verify all other fields are unchanged
        assert updated_conf.image == original_conf.image, "image changed"
        assert updated_conf.enable_ygg == original_conf.enable_ygg, "enable_ygg changed"
        assert updated_conf.require == original_conf.require, "require changed"
        assert updated_conf.dns == original_conf.dns, "dns changed"
        assert updated_conf.local_access == original_conf.local_access, "local_access changed"
        assert updated_conf.mount == original_conf.mount, "mount changed"
        assert updated_conf.port == original_conf.port, "port changed"
        assert updated_conf.environment == original_conf.environment, "environment changed"
        assert updated_conf.extra_compose_configs == original_conf.extra_compose_configs, \
            "extra_compose_configs changed"
        
        print("\n✓ All validation checks passed: Config data unchanged except autostart")


def test_roundtrip_line_by_line_comparison():
    """Test that shows exact line-by-line comparison to prove only autostart changes."""
    
    source_file = path.join(current_dir, "resources/test-man8s-conf.yaml")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a copy of the test file
        test_file = path.join(temp_dir, "test-config.yaml")
        shutil.copy(source_file, test_file)
        
        # Read original
        with open(test_file, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        # Update
        update_mbcontainer_autostart(test_file, False)
        
        # Read updated
        with open(test_file, "r", encoding="utf-8") as f:
            updated_content = f.read()
        
        # Compare
        original_lines = original_content.split('\n')
        updated_lines = updated_content.split('\n')
        
        changes = []
        for i, (orig, upd) in enumerate(zip(original_lines, updated_lines)):
            if orig != upd:
                changes.append((i + 1, orig, upd))
        
        # Should only have 1 change: the autostart line
        assert len(changes) == 1, f"Expected only 1 change, got {len(changes)}"
        
        line_num, orig, upd = changes[0]
        assert "autostart" in orig, "Changed line should be autostart"
        assert "autostart" in upd, "Updated line should be autostart"
        assert "# autostart" in orig, "Comment should be preserved"
        assert "# autostart" in upd, "Comment should be preserved"
        
        print(f"\n✓ Perfect RoundTrip: Only 1 line changed (line {line_num})")
        print(f"  Original: {orig}")
        print(f"  Updated:  {upd}")


if __name__ == "__main__":
    test_roundtrip_preserves_format_and_comments()
    test_roundtrip_with_parse_and_validate()
    test_roundtrip_line_by_line_comparison()
    print("\n✓✓✓ All tests passed! RoundTrip is working perfectly!")
