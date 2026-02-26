import json
import gradio as gr
from lxml import etree
import re
from io import BytesIO
import tempfile
import os
import zipfile
import time

from dorico_fixer import DoricoFixer

# Load data
with open("config/default_options.json", "r") as f:
    default_options = json.load(f)

with open("config/instrument_names.json", "r") as f:
    instrument_data = json.load(f)

fixer = DoricoFixer()

def process_file(files, selected_fixes):
    if files is None or len(files) == 0:
        return None, "No files uploaded"
    
    fixer.log_text = ""
    
    # Convert selected display names back to keys
    options_keys = list(default_options.keys())
    display_names = [default_options[opt]["display_name"] for opt in options_keys]
    name_to_key = dict(zip(display_names, options_keys))
    
    enabled_fixes = [name_to_key[name] for name in selected_fixes if name in name_to_key]
    
    temp_files = []
    temp_dir = tempfile.mkdtemp()
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        fixer.log_text += f"\n**{os.path.basename(file_path)}:** \n"
        fixed_xml, _ = fixer.fix(xml_content, default_options.copy(), instrument_data, enabled_fixes)
        
        # Get original filename and create fixed name
        original_name = os.path.basename(file_path)
        if '.' in original_name:
            base_name = original_name.rsplit('.', 1)[0]
        else:
            base_name = original_name
        fixed_filename = base_name + '_dfixed.musicxml'
        
        # Write to file in temp dir with proper name
        fixed_path = os.path.join(temp_dir, fixed_filename)
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            f.write('<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n')
            f.write(fixed_xml)
        
        temp_files.append(fixed_path)
    
    # If multiple files, also create a zip
    output_files = temp_files
    if len(temp_files) > 1:
        ltime=time.localtime()
        zip_path = os.path.join(temp_dir, f'compressed_{ltime.tm_year}{ltime.tm_mon}{ltime.tm_mday}-{ltime.tm_hour}{ltime.tm_min}{ltime.tm_sec}_dfixed.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_files:
                zipf.write(file_path, os.path.basename(file_path))
        output_files.append(zip_path)

    return output_files, fixer.get_log_text()

# Gradio Interface
with gr.Blocks(title="DFix - MusicXML Processor") as demo:
    gr.Markdown("# DFix - MusicXML Processor")
    gr.Markdown("Upload MusicXML files and select the fixes to apply.")
    
    file_input = gr.File(label="Upload MusicXML Files", file_types=[".xml", ".musicxml"], file_count="multiple")
    
    with gr.Accordion("Select Fixes", open=True):
        options = list(default_options.keys())
        display_names = [default_options[opt]["display_name"] for opt in options]
        
        # Select only those with run: true
        selected_fixes = [default_options[opt]["display_name"] for opt in options if default_options[opt]["run"]]
        
        checkboxes = gr.CheckboxGroup(
            choices=display_names,
            label="",
            value=selected_fixes
        )
    
    process_btn = gr.Button("Process Files")
    
    download_output = gr.File(label="Download Fixed Files", file_count="multiple")
    
    with gr.Accordion("Processing Log", open=False) as p_log:
        # log_output = gr.Textbox(label="logs", lines=10)
        # log_output = gr.Code(lines=10, language="markdown")
        log_output = gr.Markdown(label="Log Out")

    process_btn.click(
        fn=process_file,
        inputs=[file_input, checkboxes],
        outputs=[download_output, log_output]
    )

if __name__ == "__main__":
    demo.launch()