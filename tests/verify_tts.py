import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tts import TTSFactory

async def test_tts_provider():
    print("Testing TTS Provider...")
    
    try:
        # 1. Test Factory
        provider = TTSFactory.get_provider("edge")
        print(f"✅ Provider obtained: {type(provider).__name__}")
        
        # 2. Test Voices
        voices = provider.get_voices()
        print(f"✅ Voice list retrieved: {len(voices)} voices available")
        print(f"First voice: {voices[0]['name']}")
        
        # 3. Test Generation
        output_file = "test_audio.mp3"
        print(f"Generating audio to {output_file}...")
        success = await provider.generate_audio("你好，这是一个测试音频。", "xiaoxiao", output_file)
        
        if success and Path(output_file).exists():
            print("✅ Audio generation successful")
            # Cleanup
            Path(output_file).unlink()
        else:
            print("❌ Audio generation failed")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tts_provider())
