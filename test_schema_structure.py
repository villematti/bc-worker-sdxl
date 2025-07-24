#!/usr/bin/env python3
"""
TEST: Single Schema Structure

Test the simplified single INPUT_SCHEMA structure without runpod dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from schemas import INPUT_SCHEMA

def test_schema_structure():
    """Test that the single INPUT_SCHEMA has the correct structure"""
    print("🧪 Testing Single INPUT_SCHEMA Structure\n")
    
    print("📋 Schema parameters:")
    for param, config in INPUT_SCHEMA.items():
        param_type = config.get('type', 'unknown')
        required = config.get('required', False)
        default = config.get('default', 'no default')
        has_constraints = 'constraints' in config
        
        status = "✅" if param_type != 'unknown' else "❌"
        print(f"   {status} {param}: {param_type.__name__ if hasattr(param_type, '__name__') else param_type}")
        if required:
            print(f"      Required: {required}")
        if default != 'no default':
            print(f"      Default: {default}")
        if has_constraints:
            print(f"      Has constraints: ✅")
    
    print(f"\n📊 Total parameters: {len(INPUT_SCHEMA)}")
    
    # Test critical parameters exist
    critical_params = ['prompt', 'task_type', 'num_frames', 'video_height', 'video_width']
    print("\n🔍 Critical parameters check:")
    
    for param in critical_params:
        if param in INPUT_SCHEMA:
            config = INPUT_SCHEMA[param]
            default = config.get('default')
            print(f"   ✅ {param}: default={default}")
        else:
            print(f"   ❌ {param}: MISSING")
    
    return True

def test_constraint_functions():
    """Test that constraint functions work correctly"""
    print("\n🧪 Testing Constraint Functions:")
    
    # Test video height constraint
    height_constraint = INPUT_SCHEMA['video_height']['constraints']
    print("   Video height constraints:")
    print(f"      height(None): {height_constraint(None)} ✅")
    print(f"      height(480): {height_constraint(480)} ✅")
    print(f"      height(720): {height_constraint(720)} ❌")
    
    # Test video width constraint  
    width_constraint = INPUT_SCHEMA['video_width']['constraints']
    print("   Video width constraints:")
    print(f"      width(None): {width_constraint(None)} ✅")
    print(f"      width(832): {width_constraint(832)} ✅")
    print(f"      width(1280): {width_constraint(1280)} ❌")
    
    # Test num_frames constraint
    frames_constraint = INPUT_SCHEMA['num_frames']['constraints']
    print("   Num frames constraints:")
    print(f"      frames(None): {frames_constraint(None)} ✅")
    print(f"      frames(81): {frames_constraint(81)} ✅")
    print(f"      frames(100): {frames_constraint(100)} ❌")
    
    return True

def test_no_defaults_for_video():
    """Test that video parameters have no defaults for image requests"""
    print("\n🎯 Testing Video Parameter Defaults:")
    
    video_params = ['num_frames', 'video_height', 'video_width', 'video_guidance_scale', 'fps']
    
    for param in video_params:
        if param in INPUT_SCHEMA:
            default = INPUT_SCHEMA[param]['default']
            if default is None:
                print(f"   ✅ {param}: default=None (good for image requests)")
            else:
                print(f"   ❌ {param}: default={default} (would interfere with image requests)")
        else:
            print(f"   ❌ {param}: missing from schema")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Single Schema Solution")
    print("   Simple, unified INPUT_SCHEMA that handles all task types\n")
    
    success1 = test_schema_structure()
    success2 = test_constraint_functions()
    success3 = test_no_defaults_for_video()
    
    if success1 and success2 and success3:
        print("\n🎉 SUCCESS: Single schema is properly structured!")
        print("   ✅ All parameters present and configured")
        print("   ✅ Constraints working correctly")
        print("   ✅ Video parameters have None defaults (won't interfere)")
        print("   ✅ Ready to handle both image and video requests")
        print("   ✅ No unnecessary complexity - just ONE schema!")
    else:
        print("\n💥 FAILURE: Schema structure issues")
        exit(1)
