#!/usr/bin/env python3
"""
Test script for plugin validation system.

This script demonstrates the plugin validation functionality
by testing valid and invalid plugin implementations.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from crypto_bot.plugins.registry import ExchangePluginRegistry, PluginValidationError, PluginLoadError
from crypto_bot.plugins.exchanges.test_validation import (
    ValidExchangePlugin,
    InvalidExchangePlugin,
    IncompleteExchangePlugin
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_plugin_validation():
    """Test the plugin validation system."""
    print("🧪 Testing Plugin Validation System")
    print("=" * 50)
    
    # Create registry
    registry = ExchangePluginRegistry()
    
    # Test 1: Valid plugin
    print("\n1️⃣ Testing Valid Plugin")
    print("-" * 30)
    try:
        # Test direct instantiation
        valid_plugin = ValidExchangePlugin()
        print(f"✅ Valid plugin instantiated: {valid_plugin}")
        
        # Test validation
        registry._validate_plugin(ValidExchangePlugin)
        print("✅ Valid plugin passed validation")
        
        # Test plugin info
        info = registry._get_plugin_name(ValidExchangePlugin)
        print(f"✅ Plugin name: {info}")
        
    except Exception as e:
        print(f"❌ Valid plugin failed: {e}")
    
    # Test 2: Invalid plugin (missing attributes)
    print("\n2️⃣ Testing Invalid Plugin (Missing Attributes)")
    print("-" * 50)
    try:
        registry._validate_plugin(InvalidExchangePlugin)
        print("❌ Invalid plugin should have failed validation")
    except PluginValidationError as e:
        print(f"✅ Invalid plugin correctly rejected: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
    
    # Test 3: Incomplete plugin (missing methods)
    print("\n3️⃣ Testing Incomplete Plugin (Missing Methods)")
    print("-" * 50)
    try:
        registry._validate_plugin(IncompleteExchangePlugin)
        print("❌ Incomplete plugin should have failed validation")
    except PluginValidationError as e:
        print(f"✅ Incomplete plugin correctly rejected: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
    
    # Test 4: Plugin loading from directory
    print("\n4️⃣ Testing Plugin Loading from Directory")
    print("-" * 40)
    try:
        # Set plugin directory to the test directory
        test_plugin_dir = Path(__file__).parent / "src" / "crypto_bot" / "plugins" / "exchanges"
        registry = ExchangePluginRegistry(str(test_plugin_dir))
        
        # Load plugins
        registry.load_plugins()
        print(f"✅ Loaded {len(registry.plugins)} plugins")
        
        # List available plugins
        plugin_names = registry.plugin_names
        print(f"✅ Available plugins: {plugin_names}")
        
        # Test getting plugin info
        for name in plugin_names:
            try:
                info = registry.get_exchange_info(name)
                print(f"✅ Plugin '{name}': {info['name']} v{info['version']}")
            except Exception as e:
                print(f"⚠️ Error getting info for '{name}': {e}")
        
    except Exception as e:
        print(f"❌ Plugin loading failed: {e}")
    
    # Test 5: Plugin instantiation
    print("\n5️⃣ Testing Plugin Instantiation")
    print("-" * 35)
    try:
        if registry.plugins:
            plugin_name = list(registry.plugins.keys())[0]
            print(f"Testing instantiation of: {plugin_name}")
            
            # Create instance
            instance = registry.create_instance(plugin_name, sandbox=True)
            print(f"✅ Created instance: {instance}")
            
            # Test initialization
            await instance.initialize()
            print("✅ Plugin initialized successfully")
            
            # Test some methods
            markets = await instance.load_markets()
            print(f"✅ Loaded markets: {len(markets)} markets")
            
            # Close the instance
            await instance.close()
            print("✅ Plugin closed successfully")
            
        else:
            print("⚠️ No plugins available for instantiation test")
            
    except Exception as e:
        print(f"❌ Plugin instantiation failed: {e}")
    
    print("\n🎉 Plugin Validation Test Complete!")


async def main():
    """Main test function."""
    try:
        await test_plugin_validation()
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
