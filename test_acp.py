"""Test script for ACP HTTP functionality."""

import asyncio
import sys

# Add backend/packages/harness to path
sys.path.insert(0, "/root/.openclaw/workspace/deer-flow/backend/packages/harness")

from deerflow.tools.builtins.invoke_acp_agent_tool import _OpenCodeHTTPClient


async def test_acp_http_connection():
    """Test connection to remote OpenCode ACP service at http://47.102.205.195:3000."""

    print("Testing ACP HTTP connection to http://47.102.205.195:3000...")

    client = _OpenCodeHTTPClient("http://47.102.205.195:3000")

    try:
        # Test create session
        print("\n1. Creating session...")
        session_id = await client.create_session(agent="build", directory="/tmp")
        print(f"   ✓ Session created: {session_id}")

        # Test send message
        print("\n2. Sending test message...")
        response = await client.send_message(
            session_id, "Hello from DeerFlow test script!", agent="build"
        )
        print(f"   ✓ Got response ({len(response)} characters):")
        print(f"   --- Response start ---\n{response[:500]}")
        if len(response) > 500:
            print("   ... (truncated)")
        print("   --- Response end ---")

        print("\n✅ ACP HTTP test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_acp_http_connection())
    sys.exit(0 if success else 1)
