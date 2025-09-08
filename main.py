# Constantes
VIDEO_PATH = "subway_surfer.mp4"  # Chemin vers votre vidéo de fond
PREPROMPT = """Tu es un créateur de vidéo 'brainrot', transforme ce texte en un texte type brainrot, avec un vocabulaire adapté à la génération alpha en français. Le texte sera lu tel-quel, pas de formatage. Tout est dit par un seul personnage : le narrateur. reste factuel, n'insulte pas les gens'"""
MODEL = "qwen3:8b"

import ollama
import os
import re
import tempfile
import shutil
from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips, CompositeVideoClip
from moviepy.video.VideoClip import TextClip

from gtts import gTTS  # Google TTS

import time

def word_timestamps(text, audio_clips):
    """
    Calcule les timestamps précis pour chaque mot en se basant
    sur la durée réelle de chaque segment audio
    """
    # Nettoyage du texte
    clean_text = ' '.join(text.split())

    # Calcul de la durée totale de l'audio
    total_audio_duration = sum(clip.duration for clip in audio_clips)

    # Calcul de la vitesse de parole moyenne en français
    words = clean_text.split()
    total_words = len(words)

    if total_words == 0:
        return []

    # Calcul de la durée par mot basée sur l'audio réel
    avg_word_duration = total_audio_duration / total_words

    # Création des timestamps
    timestamps = []
    current_time = 0
    segment_index = 0
    segment_offset = 0

    for i, word in enumerate(words):
        # Calcul de la durée spécifique pour ce mot
        # Les mots longs prennent plus de temps à prononcer
        length_factor = max(1.0, len(word) / 5.0)
        word_duration = avg_word_duration * length_factor

        # Gestion des fins de phrases pour des pauses plus longues
        if word.endswith(('.', '!', '?', ':')):
            word_duration *= 1.5

        # Vérification si on doit passer au segment suivant
        if segment_index < len(audio_clips) - 1 and current_time + word_duration > segment_offset + audio_clips[segment_index].duration:
            segment_index += 1
            segment_offset = sum(clip.duration for clip in audio_clips[:segment_index])

        # Ajout du timestamp
        start_time = current_time
        end_time = current_time + word_duration
        timestamps.append((word, start_time, end_time))

        current_time = end_time

    return timestamps


def create_word_by_word_subtitles(generated_text, audio_clips, video_size):
    """
    Crée des sous-titres où chaque mot apparaît un par un
    """
    # Génère les timestamps pour chaque mot
    word_timestamps_list = word_timestamps(generated_text, audio_clips)

    # Crée un clip texte pour chaque mot
    word_clips = []
    for word, start_time, end_time in word_timestamps_list:
        word_clip = TextClip(
            text=word.upper(),  # En majuscules pour l'effet brainrot
            font="FreeSans",
            font_size=200,
            color="white",
            bg_color="black",
            margin=(10,10)
        )

        # Positionne le mot au centre bas de l'écran
        word_clip = word_clip.with_position(("center", "center"))
        word_clip = word_clip.with_start(start_time).with_duration(end_time - start_time)

        word_clips.append(word_clip)

    return word_clips


def main():
    # Vérification que le chemin de la vidéo est spécifié
    if not VIDEO_PATH:
        raise ValueError("VIDEO_PATH doit être défini dans les constantes")

    # 1. Génération de texte avec Ollama
    print(f"Génération de texte avec {MODEL}...")

    # Lecture du document texte source
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            input_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("Le fichier input.txt est requis pour la génération de texte")

    full_prompt = f"{PREPROMPT}\n\n---\n\n{input_text}"

    # Génération avec Ollama

    response = ollama.generate(
        model=MODEL,
        prompt=full_prompt
    )
    generated_text = response["response"]


    print(f"Texte généré : {generated_text[:200]}...")

    # Sauvegarde du texte généré
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(generated_text)

    # Nettoyage du texte généré
    splitted_generated_text = generated_text.split("</think>")
    if len(splitted_generated_text) == 2:
        generated_text = splitted_generated_text[1].strip()
    else:
        generated_text = splitted_generated_text[0].strip()

    # 2. GÉNÉRATION DE PLUSIEURS SEGMENTS AUDIO AVEC GTTS
    print("Génération de la synthèse vocale avec gTTS...")

    # Création d'un dossier temporaire pour les segments audio
    temp_dir = tempfile.mkdtemp()

    try:
        # Diviser le texte en segments (séparés par deux sauts de ligne)
        segments = [s.strip() for s in generated_text.split("\n\n") if s.strip()]
        print(f"Texte divisé en {len(segments)} segments")

        # Générer un audio pour chaque segment avec gTTS
        audio_segments = []
        audio_clips = []
        for i, segment in enumerate(segments):
            print(f"Génération du segment {i+1}/{len(segments)}...")
            print(f"Contenu: {segment[:50]}...")

            # UTILISATION DE GTTS
            tts = gTTS(text=segment, lang='fr')
            segment_path = os.path.join(temp_dir, f"segment_{i}.mp3")
            tts.save(segment_path)

            # Charger immédiatement le clip audio pour obtenir sa durée précise
            clip = AudioFileClip(segment_path)
            audio_clips.append(clip)
            audio_segments.append(segment_path)

        # Combiner tous les segments audio
        print("Combinaison des segments audio...")
        final_audio = concatenate_audioclips(audio_clips)
        final_audio.write_audiofile("output_audio.mp3")  # Format MP3 pour gTTS
        audio_duration = final_audio.duration

        # 3. Liaison TTS sur fond vidéo
        print("Intégration de l'audio dans la vidéo...")
        video = VideoFileClip(VIDEO_PATH)

        # Ajustement de la durée de la vidéo à celle de l'audio
        if video.duration > audio_duration:
            video = video.subclipped(0, audio_duration)

        video = video.with_audio(final_audio)

        # 4. SOUS-TITRAGE MOT PAR MOT SYNCHRONISÉ
        print("Création des sous-titres mot par mot synchronisés...")

        # Créer les sous-titres où chaque mot apparaît un par un, synchronisés avec l'audio
        word_clips = create_word_by_word_subtitles(generated_text, audio_clips, video.size)

        # Fusion de la vidéo et des sous-titres
        print("Assemblage de la vidéo finale...")
        final_video = CompositeVideoClip([video] + word_clips)

        # Export de la vidéo finale
        output_video = "video_finale.mp4"
        final_video.write_videofile(
            output_video,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            threads=4,
            fps=24
        )

        print(f"Processus terminé ! Vidéo générée : {output_video}")

    finally:
        # Nettoyage des fichiers temporaires
        print("Nettoyage des fichiers temporaires...")
        shutil.rmtree(temp_dir)

    # Nettoyage du fichier audio temporaire
    if os.path.exists("output_audio.mp3"):
        os.remove("output_audio.mp3")

    # Fermeture propre des ressources
    for clip in audio_clips:
        clip.close()
    video.close()
    final_audio.close()
    final_video.close()

if __name__ == "__main__":
    main()
