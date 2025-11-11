"""
Test script for suno/bark-small model with Italian language
"""
import os
import torch
from transformers import pipeline
from transformers import AutoProcessor, AutoModelForTextToWaveform
import scipy.io.wavfile as wavfile

# Test Italian text
ita_text = '''
Chicago 1993. Elizabeth e Jack sono arrivati nella grande metropoli a vent'anni, due origini molto diverse, ma lo stesso obiettivo di costruirsi una vita. La città è effervescente, in piena trasformazione, tante sono le spinte verso una nuova scena culturale. I due ragazzi vivono in due piccoli appartamenti in un quartiere bohémien, dove artisti e studenti infondono linfa giovane a una vecchia area industriale. Fin qui, non si conoscono. Ma le loro finestre affacciano sullo stesso vicolo e la sera, quando le luci si accendono, si accendono anche le loro vite intime: lei sfoglia pesanti manuali alla luce di una candela, accanto un bicchiere di vino, lui mescola colori e solventi, ispeziona negativi con la lente di ingrandimento. Elizabeth studia psicologia, Jack è fotografo. È inverno e si osservano.

Una sera, a un concerto, Jack si fa coraggio e avvicina Elizabeth invitandola a bere qualcosa. Il periodo dell'università vissuto insieme è esaltante, ma a distanza di vent'anni, dopo il matrimonio, dopo un figlio, cosa resta? Oggi, i risparmi investiti nell'appartamento all'ultimo piano di un ex cantiere navale e i progetti di ristrutturazione rivelano i cedimenti dei loro sogni. Elizabeth, ad esempio, vorrebbe due camere da letto e due ingressi separati, mentre Jack non ne capisce il senso. Ecco il benessere ottenuto.
'''

# Shorter test text for quick testing
short_ita_text = "Ciao, mi chiamo Elizabeth e studio psicologia all'università di Chicago. Questo è un test del modello suno/bark-small per la lingua italiana."


def test_with_pipeline(text, output_path):
    """Test using pipeline approach"""
    print(f"\n{'='*60}")
    print("Testing suno/bark-small with pipeline approach")
    print(f"{'='*60}\n")
    
    print("Loading pipeline...")
    pipe = pipeline("text-to-speech", model="suno/bark-small")
    
    print("Generating speech...")
    output = pipe(text)
    
    # Extract audio array and sample rate
    audio_array = output["audio"]
    sample_rate = output["sampling_rate"]
    
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio_array.shape}")
    
    # Save to file
    print(f"Saving to: {output_path}")
    wavfile.write(output_path, sample_rate, audio_array)
    print("✓ Audio saved successfully!\n")
    
    return audio_array, sample_rate


def test_with_direct_loading(text, output_path):
    """Test using direct model loading approach"""
    print(f"\n{'='*60}")
    print("Testing suno/bark-small with direct loading approach")
    print(f"{'='*60}\n")
    
    print("Loading processor and model...")
    processor = AutoProcessor.from_pretrained("suno/bark-small")
    model = AutoModelForTextToWaveform.from_pretrained("suno/bark-small")
    
    # Move model to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Using device: {device}")
    
    print("Processing text...")
    inputs = processor(
        text=[text],
        return_tensors="pt",
    ).to(device)
    
    print("Generating speech...")
    with torch.no_grad():
        audio_array = model.generate(**inputs, pad_token_id=10000)
    
    # Convert to numpy and get sample rate
    audio_array = audio_array.cpu().numpy().squeeze()
    sample_rate = model.generation_config.sample_rate
    
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio_array.shape}")
    
    # Save to file
    print(f"Saving to: {output_path}")
    wavfile.write(output_path, sample_rate, audio_array)
    print("✓ Audio saved successfully!\n")
    
    return audio_array, sample_rate


if __name__ == "__main__":
    # Create output directory if it doesn't exist
    output_dir = "audio_output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("Testing suno/bark-small model for Italian language")
    print("="*60)
    
    # Test 1: Pipeline approach with short text
    print("\n[Test 1] Pipeline approach with short text")
    try:
        test_with_pipeline(
            short_ita_text,
            os.path.join(output_dir, "bark_small_pipeline_short.wav")
        )
    except Exception as e:
        print(f"✗ Error in pipeline test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Direct loading approach with short text
    print("\n[Test 2] Direct loading approach with short text")
    try:
        test_with_direct_loading(
            short_ita_text,
            os.path.join(output_dir, "bark_small_direct_short.wav")
        )
    except Exception as e:
        print(f"✗ Error in direct loading test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Pipeline approach with longer text (optional)
    print("\n[Test 3] Pipeline approach with longer text")
    try:
        test_with_pipeline(
            ita_text[:500],  # First 500 characters
            os.path.join(output_dir, "bark_small_pipeline_long.wav")
        )
    except Exception as e:
        print(f"✗ Error in pipeline long text test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Testing completed!")
    print("="*60 + "\n")
