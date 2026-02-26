---
title: DFix - MusicXML Processor
emoji: 🎵
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---

# DFix - MusicXML Processor

A Python web application that replicates the functionality of the Electron-based Dorico Fixer. This tool processes MusicXML files to apply various fixes for better compatibility with Dorico music notation software.

## Features

The application can apply the following fixes to MusicXML files:

- **Fix the Clef**: Adds percussion clef if missing
- **Fix the Ghost Note**: Adds parentheses to ghost snare drum notes
- **Fix the Crash Notehead**: Changes crash cymbal noteheads to ornate X
- **Fix the Hi-hat Notehead**: Changes hi-hat closed noteheads to X
- **Fix the Word to Rehearsal**: Converts certain text elements to rehearsal marks
- **Fix the Placement Change**: Adjusts placement of direction elements
- **Fix the BPM Remover**: Removes BPM indications
- **Add a MIDI map**: Adds MIDI instrument mappings for drum kit
- **Fix the Beat Unit Changings**: Converts metronome markings to text
- **Fix the Buzz Roll**: Converts buzz roll notations to tremolo
- **Fix the Swing Marks**: Converts swing markings to proper metronome notation
- **Remove Single Multi-measure Rests**: Converts single measure rests to regular rests
- **Convert Sticking to Lyrics**: Adds zero-width spaces for sticking notation
- **Fix time-modification based on tuplet**: Adds time modification from tuplet data
- **Remove the Prevent New Systems**: Removes system break prevention

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```bash
   python app.py
   ```

2. Open the web interface in your browser (usually http://localhost:7860)

3. Upload a MusicXML file (.xml or .musicxml)

4. Select the fixes you want to apply

5. Click "Process File"

6. Download the processed file

## Dependencies

- gradio: For the web interface.
- lxml: For XML parsing and manipulation.

## Original Project

## This is a Python port of the [electron-dorico-fixer](https://github.com/seppe-vs/electron-dorico-fixer) Electron application.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
