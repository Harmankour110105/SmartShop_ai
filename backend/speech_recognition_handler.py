import speech_recognition as sr
from fastapi import APIRouter, HTTPException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["speech"])

@router.post("/recognize/mic")
async def recognize_from_mic():
    """Endpoint to recognize speech from microphone input."""
    recognizer = sr.Recognizer()
    
    try:
        # List available microphones
        mics = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphones: {mics}")
        
        # Use default microphone with specific sample rate and chunk size
        with sr.Microphone(sample_rate=16000, chunk_size=1024) as source:
            logger.info("Microphone initialized successfully")
            
            # Adjust the recognizer sensitivity to ambient noise
            logger.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Set recognition parameters
            recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.6  # Shorter pause threshold
            recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider the speaking audio a phrase
            recognizer.non_speaking_duration = 0.4  # Seconds of non-speaking audio to keep on both sides of the recording
            
            logger.info("Listening for speech...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            logger.info(f"Audio captured successfully. Duration: {len(audio.frame_data) / audio.sample_rate:.2f} seconds")
            logger.info(f"Sample rate: {audio.sample_rate}Hz")
            
            try:
                # Try with language specification
                text = recognizer.recognize_google(audio, language='en-US')
                logger.info(f"Successfully recognized text: {text}")
                return {"text": text}
            except sr.UnknownValueError:
                logger.error("Google Speech Recognition could not understand the audio")
                raise HTTPException(status_code=400, detail="Could not understand audio. Please speak clearly and try again.")
            except sr.RequestError as e:
                logger.error(f"Could not request results from Google Speech Recognition service: {str(e)}")
                raise HTTPException(status_code=503, detail=f"Speech recognition service error: {str(e)}")
            
    except sr.WaitTimeoutError:
        logger.error("Listening timed out")
        raise HTTPException(status_code=408, detail="Listening timed out. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error during speech recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech recognition error: {str(e)}") 