
import pytest
import asyncio
import os
from app.api.routers.auth import delete_vercel_blob
from app.core.config import settings

# URL provided by the user to delete
TARGET_BLOB_URL = "https://8zrq1svqawat0uuy.public.blob.vercel-storage.com/nib_document/pixel-napping.png"

@pytest.mark.asyncio
async def test_delete_specific_blob():
    """
    Test the delete_vercel_blob function using the specific URL provided.
    This test verifies that the function can successfully call the Vercel SDK
    to delete the file.
    """
    # Ensure we have the token
    if not settings.BLOB_READ_WRITE_TOKEN:
        pytest.skip("BLOB_READ_WRITE_TOKEN not set in environment")

    print(f"\nAttempting to delete blob: {TARGET_BLOB_URL}")
    print(f"Using Token: {settings.BLOB_READ_WRITE_TOKEN[:5]}... (masked)")

    # Call the function
    # Note: vercel_blob.delete returns None on success or raises an error
    try:
        await delete_vercel_blob(TARGET_BLOB_URL)
        print("✅ Function execution completed successfully (no errors raised).")
        
        # Verify SDK import worked by checking logs logic implicitly 
        from vercel_blob import delete
        print("✅ verified 'vercel_blob' SDK is installed and importable.")
        
    except Exception as e:
        pytest.fail(f"Failed to delete blob: {e}")

if __name__ == "__main__":
    # Allow running this script directly
    asyncio.run(test_delete_specific_blob())
