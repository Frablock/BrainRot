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

from gtts import gTTS  # ✅ UTILISATION DE GTTS AU LIEU DE BARK

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
            bg_color="black"
        )

        # Positionne le mot au centre bas de l'écran
        word_clip = word_clip.with_position(("center", 0.85), relative=True)
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
    """
    response = ollama.generate(
        model=MODEL,
        prompt=full_prompt
    )
    generated_text = response["response"]
    """
    generated_text = """<think>
Okay, I need to transform the given text into a "brainrot" style in French, suitable for an alpha generation audience. The user wants the text to be read as-is without any formatting, and it should be factual, not insulting. The narrator is the only character, so the text should be in first person or a consistent voice.

First, I'll read through the original text to understand the key points. It's about Marine Le Pen and the National Rally (RN) being convicted for illegal activities, including falsifying contracts to pay non-working staff. The text mentions the court's decision, the legal basis for the conviction, the ineligibility penalty, and the potential impact on her 2027 presidential bid. There's also a reference to a 2013 video where she talks about life imprisonment for those convicted using their mandate.

Now, "brainrot" style typically uses repetitive, catchy phrases, maybe some slang, and a fast-paced delivery. It should be engaging, maybe with some dramatic emphasis. Since the audience is alpha generation, the language should be modern, perhaps with some internet slang or abbreviations, but the user specified not to insult people, so need to keep it respectful.

I need to maintain the factual content but present it in a more engaging, maybe even a bit humorous way. Use phrases like "C'est pas des blagues, les gars" or "Y a pas de doute" to make it more relatable. Also, structure the information in short, punchy sentences. Maybe use some rhetorical questions or emphatic statements.

Check for any parts that might be too formal and rephrase them. Ensure that the legal terms are explained in simpler terms. Avoid any direct insults but use sarcasm or irony if it doesn't come off as offensive. Make sure the flow is smooth, with transitions between different points of the text.

Also, the user mentioned that the text will be read as-is, so I shouldn't add any markdown. Just plain text. Let me start by breaking down the original text into key sections: the conviction details, the legal arguments, the ineligibility penalty, the 2027 election impact, and the 2013 video reference.

For each section, I'll rephrase using brainrot style. Use repetition for emphasis, maybe some exclamations. For example, "Y a pas de doute, les gars, c'est pas des blagues" for the conviction part. For the legal arguments, maybe "Le tribunal a pas de doute, c'est pas des blagues" to keep the structure similar.

Make sure to maintain the factual accuracy but present it in a more engaging way. Avoid any negative terms that could be seen as insulting. Use phrases like "C'est pas de la chance, les gars" to imply that the outcome is justified without being harsh.

Check for consistency in the narrator's voice, ensuring it's a single character throughout. Use contractions and colloquial expressions to make it sound natural. Maybe add some phrases like "C'est clair, les gars" to emphasize points.

Finally, review the entire text to ensure it's in line with the brainrot style, stays factual, and doesn't insult anyone. Make sure the flow is smooth and the information is clearly conveyed in a more engaging manner.
</think>

C'est pas des blagues, les gars, Marine Le Pen et le Rassemblement national ont fait du mensonge leur arme de prédilection. Sur les faits, le tribunal a pas de doute, c'est pas des blagues. Leur « exceptionnel » peine d'inéligibilité, leur « absence » de fondements juridiques, c'est de la manipulation. Et c'est pas fini, les gars, parce que les faits sont clairs : 40 contrats d'assistants parlementaires, c'est pas des blagues, c'est des salarés du parti qui travaillent pas pour les eurodéputés.

Marine Le Pen, qui se dit « totalement innocente », a dit sur TF1 le 31 mars que c'était juste un « désaccord administratif ». Mais le tribunal a pas de doute, c'est pas des blagues. Les prévenus ont pas vu les règles européennes comme des règles, c'est pas des blagues. Ils décidaient seuls, avec le parti et les parlementaires, de faire des gardes du corps, des meetings, des trucs de l'élection locale. « C'est pas des erreurs administratives », a dit le tribunal, c'est pas des blagues. C'est un conflit avec le règlement du Parlement européen et le Code pénal.

Le risque de récidive, les gars, c'est pas des blagues. Le tribunal a dit qu'ils ont pas voulu la vérité, c'est pas des blagues. Et même si c'était pas des blagues, ils refusent de reconnaître l'illégalité de leurs actes. Le tribunal a dit que c'est pas des blagues, c'est un système pour rémunérer des gens qui travaillent pas pour les députés.

La condamnation, c'est pas des blagues, les gars. Le tribunal a pas de doute, c'est pas des blagues. Le risque de récidive, les gars, c'est pas des blagues. Le tribunal a dit qu'ils refusent de reconnaître l'illégalité, c'est pas des blagues. Et la peine d'inéligibilité, c'est pas des blagues, les gars. Le tribunal a dit que c'était une limite prévue par le législateur, c'est pas des blagues. Et c'est pas des blagues, les gars, c'est une atteinte à la démocratie.

L'exécution provisoire, c'est pas des blagues, les gars. Le tribunal a dit qu'il y a un risque de récidive, c'est pas des blagues. Et que si Marine Le Pen est condamnée à l'inéligibilité, elle ne pourra pas être candidate en 2027, c'est pas des blagues. Le ministère de la Justice a dit que 16 364 mesures d'inéligibilité ont été prononcées en 2023, c'est pas des blagues.

Et en 2013, sur Public Sénat, Marine Le Pen a dit qu'il fallait mettre en place l'inéligibilité à vie pour ceux qui ont été condamnés grâce à leur mandat, c'est pas des blagues. Et aujourd'hui, les gars, c'est pas des blagues, les juges ont dit que c'est pas des blagues. C'est pas des blagues, les gars, c'est la justice qui a dit que c'est pas des blagues."""


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

            # ✅ UTILISATION DE GTTS
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
        final_audio.write_audiofile("output_audio.mp3")  # ✅ Format MP3 pour gTTS
        audio_duration = final_audio.duration

        # 3. Liaison TTS sur fond vidéo
        print("Intégration de l'audio dans la vidéo...")
        video = VideoFileClip(VIDEO_PATH)

        # Ajustement de la durée de la vidéo à celle de l'audio
        if video.duration > audio_duration:
            video = video.subclipped(0, audio_duration)  # ✅ Correction de subclipped à subclip

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
