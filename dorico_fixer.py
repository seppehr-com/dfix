from lxml import etree
import re

class DoricoFixer:
    def __init__(self):
        self.log_text = ""

    def append_log(self, step_name, success, message=""):
        status = "✓" if success else "✗"
        self.log_text += f"{status} {step_name}\n"
        if message:
            self.log_text += f"   {message}\n"

    def validate_xml(self, xml_content):
        try:
            etree.fromstring(xml_content.encode('utf-8'))
            return {"valid": True}
        except etree.XMLSyntaxError as e:
            return {"valid": False, "error": str(e)}

    def apply_step(self, step_name, current_xml, transform_fn):
        before = current_xml
        try:
            after = transform_fn(before)
        except Exception as e:
            self.append_log(step_name, False, f"Exception: {str(e)}")
            return before

        validation = self.validate_xml(after)
        if validation["valid"]:
            self.append_log(step_name, True)
            return after
        else:
            self.append_log(step_name, False, validation["error"])
            return before

    def get_log_text(self):
        return self.log_text.strip()

    def fix(self, xml_content, options, instrument_data, enabled_fixes):
        fixed = xml_content

        # Make options based on user's selection
        if enabled_fixes is not None and len(enabled_fixes) > 0:
            for key in options:
                if key in options and isinstance(options[key], dict) and "run" in options[key]:
                    options[key]["run"] = key in enabled_fixes

        if options["p_clef"]["run"]:
            fixed = self.apply_step("p_clef_fix", fixed, lambda xml: self.p_clef_fix(xml, options["p_clef"]["sign"], options["p_clef"]["visibility"]))

        if options["ghost_note"]["run"]:
            fixed = self.apply_step("ghost_note_fix", fixed, lambda xml: self.ghost_note_fix(xml, instrument_data["ghost_snare_drum"]["names"]))

        if options["crash_notehead"]["run"]:
            fixed = self.apply_step("crash_notehead_fix", fixed, lambda xml: self.crash_notehead_fix(
                xml,
                instrument_data["normal_crash_cymbal"]["names"],
                instrument_data["choked_crash_cymbal"]["names"],
                options["crash_notehead"]["notehead_type"]
            ))

        if options["hihat_notehead"]["run"]:
            fixed = self.apply_step("hihat_notehead_fix", fixed, lambda xml: self.hihat_notehead_fix(xml, instrument_data["hi_hat_closed"]["names"]))

        if options["word_to_rehearsal"]["run"]:
            # For finale format
            fixed = self.apply_step("word_to_rehearsal_for_finale", fixed, lambda xml: self.word_to_rehearsal(xml, {
                "font-family": "Times",
                "font-size": "12",
                "font-weight": "bold",
            }))
            # For old format
            fixed = self.apply_step("word_to_rehearsal_old", fixed, lambda xml: self.word_to_rehearsal(xml, {
                "font-family": "Times New Roman",
                "font-size": "12",
                "font-weight": "bold",
            }))
            fixed = self.apply_step("word_to_rehearsal_old", fixed, lambda xml: self.word_to_rehearsal(xml, {
                "font-family": "Times New Roman",
                "font-size": "12",
                "valign": "top",
            }))
            # For new format
            fixed = self.apply_step("word_to_rehearsal_new", fixed, lambda xml: self.word_to_rehearsal(xml, {
                "font-family": "Arial",
                "font-size": "10",
                "font-weight": "bold",
            }))
            fixed = self.apply_step("word_to_rehearsal_new", fixed, lambda xml: self.word_to_rehearsal(xml, {
                "font-family": "Arial",
                "font-size": "10",
                "valign": "top",
            }))

        if options["placement_change"]["run"]:
            fixed = self.apply_step("placement_change", fixed, lambda xml: self.placement_change(xml, {
                "font-family": "Times New Roman",
                "font-size": "12",
            }, "below"))
            fixed = self.apply_step("placement_change", fixed, lambda xml: self.placement_change(xml, {
                "font-family": "Times New Roman",
                "font-size": "10",
            }, "below"))
            fixed = self.apply_step("placement_change", fixed, lambda xml: self.placement_change(xml, {
                "font-family": "Times New Roman",
                "font-size": "10",
                "font-style": "italic",
            }, "below"))

        if options["bpm_remover"]["run"]:
            fixed = self.apply_step("bpm_remover", fixed, lambda xml: self.bpm_remover(xml))

        if options["midi_fix"]["run"]:
            fixed = self.apply_step("midi_fix", fixed, lambda xml: self.midi_fix(xml, instrument_data))

        if options["beat_unit_changings_fix"]["run"]:
            fixed = self.apply_step("beat_unit_changings_fix", fixed, lambda xml: self.beat_unit_changings_fix(xml))

        if options["buzz_roll_fix"]["run"]:
            fixed = self.apply_step("buzz_roll_fix", fixed, lambda xml: self.buzz_roll_fix(xml))

        if options["swing_marks_fix"]["run"]:
            fixed = self.apply_step("swing_marks_fix", fixed, lambda xml: self.swing_marks_fix(xml))

        if options["remove_single_multimeasure_rests"]["run"]:
            fixed = self.apply_step("remove_single_multimeasure_rests", fixed, lambda xml: self.remove_single_multimeasure_rests(xml))

        if options["sticking_to_lyrics"]["run"]:
            fixed = self.apply_step("sticking_to_lyrics", fixed, lambda xml: self.sticking_to_lyrics(xml))

        if options["remove_prevent_new_systems"]["run"]:
            fixed = self.apply_step("remove_prevent_new_systems", fixed, lambda xml: self.remove_prevent_new_systems(xml))

        if options["tuplet_based_time_modification"]["run"]:
            fixed = self.apply_step("tuplet_based_time_modification", fixed, lambda xml: self.tuplet_based_time_modification(xml))

        print("DoricoFixer Log:\n" + self.log_text)
        # Format XML before returning
        fixed = self.prettify_xml(fixed)
        return fixed, self.log_text

    def prettify_xml(self, xml_string):
        root = etree.fromstring(xml_string.encode('utf-8'))
        return etree.tostring(root, encoding='unicode', pretty_print=True)

    def p_clef_fix(self, xml, clef_type="percussion", visibility="no"):
        root = etree.fromstring(xml.encode('utf-8'))
        part = root.find(".//part[@id='P1']")
        if part is None:
            return xml

        # Find the first measure
        measure = part.find("measure")
        if measure is None:
            return xml

        # Check if attributes exist
        attributes = measure.find("attributes")
        if attributes is None:
            attributes = etree.SubElement(measure, "attributes")

        # Check if clef already exists
        clef = attributes.find("clef")
        if clef is not None:
            sign = clef.find("sign")
            if sign is not None and sign.text == clef_type:
                return xml

        # Add clef
        clef = etree.SubElement(attributes, "clef")
        clef.set("print-object", visibility)
        sign = etree.SubElement(clef, "sign")
        sign.text = clef_type

        return etree.tostring(root, encoding='unicode')

    def find_instrument_id(self, root, instrument_name):
        score_part = root.find(".//score-part[@id='P1']")
        if score_part is None:
            return None

        instruments = score_part.findall("score-instrument")
        for instr in instruments:
            name_elem = instr.find("instrument-name")
            if name_elem is None:
                continue
            actual_name = name_elem.text.strip()
            search_name = instrument_name.strip()

            if not search_name.startswith("%") or not search_name.endswith("%"):
                if actual_name.lower() == search_name.lower():
                    id_elem = instr.get("id")
                    return id_elem
            else:
                keywords = search_name[1:-1].split("%")
                lower_name = actual_name.lower()
                if all(keyword.lower() in lower_name for keyword in keywords):
                    id_elem = instr.get("id")
                    return id_elem
        return None

    def ghost_note_fix(self, xml, ghost_note_names):
        root = etree.fromstring(xml.encode('utf-8'))
        for name in ghost_note_names:
            instrument_id = self.find_instrument_id(root, name)
            if instrument_id:
                self.add_in_instrument(root, instrument_id, '<notehead parentheses="yes">normal</notehead>')
        return etree.tostring(root, encoding='unicode')

    def add_in_instrument(self, root, instrument_id, code_to_add):
        notes = root.findall(".//note")
        for note in notes:
            instruments = note.findall("instrument")
            for instr in instruments:
                if instr.get("id") == instrument_id:
                    # Parse code_to_add as XML
                    code_root = etree.fromstring(f"<wrapper>{code_to_add}</wrapper>")
                    for child in code_root:
                        note.append(child)
                    break

    def crash_notehead_fix(self, xml, normal_crash_names, choked_crash_names, notehead_type):
        root = etree.fromstring(xml.encode('utf-8'))

        for name in normal_crash_names:
            instrument_id = self.find_instrument_id(root, name)
            if instrument_id:
                self.remove_notehead_in_instrument(root, instrument_id)
                if notehead_type == "noteheadXOrnate":
                    self.add_in_instrument(root, instrument_id, '<notehead smufl="noteheadXOrnate">other</notehead>')
                else:
                    self.add_in_instrument(root, instrument_id, '<notehead>x</notehead>')

        for name in choked_crash_names:
            instrument_id = self.find_instrument_id(root, name)
            if instrument_id:
                self.remove_notehead_in_instrument(root, instrument_id)
                if notehead_type == "noteheadXOrnate":
                    self.add_in_instrument(root, instrument_id, '<notehead smufl="noteheadXOrnate" parentheses="yes">other</notehead>')
                else:
                    self.add_in_instrument(root, instrument_id, '<notehead parentheses="yes">x</notehead>')

        return etree.tostring(root, encoding='unicode')

    def remove_notehead_in_instrument(self, root, instrument_id):
        notes = root.findall(".//note")
        for note in notes:
            instruments = note.findall("instrument")
            has_instrument = any(instr.get("id") == instrument_id for instr in instruments)
            if has_instrument:
                noteheads = note.findall("notehead")
                for nh in noteheads:
                    note.remove(nh)

    def hihat_notehead_fix(self, xml, closed_hihat_names):
        root = etree.fromstring(xml.encode('utf-8'))
        for name in closed_hihat_names:
            instrument_id = self.find_instrument_id(root, name)
            if instrument_id:
                self.add_in_instrument(root, instrument_id, "<notehead>x</notehead>")
        return etree.tostring(root, encoding='unicode')

    def word_to_rehearsal(self, xml, attribute_filters):
        root = etree.fromstring(xml.encode('utf-8'))
        words = root.findall(".//words")
        for word in words:
            matches = True
            for attr, value in attribute_filters.items():
                if word.get(attr) != value:
                    matches = False
                    break
            if matches:
                word.tag = "rehearsal"
        return etree.tostring(root, encoding='unicode')

    def placement_change(self, xml, attribute_filters, new_placement):
        root = etree.fromstring(xml.encode('utf-8'))
        directions = root.findall(".//direction")
        for direction in directions:
            words = direction.findall(".//words")
            for word in words:
                matches = True
                for attr, value in attribute_filters.items():
                    if word.get(attr) != value:
                        matches = False
                        break
                if matches:
                    direction.set("placement", new_placement)
                    break
        return etree.tostring(root, encoding='unicode')

    def bpm_remover(self, xml):
        # Remove BPM words
        xml = re.sub(r'<words[^>]*font-style=["\']normal["\'][^>]*font-weight=["\']bold["\'][^>]*>[^<]*bpm[^<]*<\/words>', '', xml, flags=re.IGNORECASE)
        xml = re.sub(r'<words\s+font-family=["\']Arial["\']\s+font-size=["\']6["\']\s+valign=["\']top["\']>\s*=\s*<\/words>', '', xml, flags=re.IGNORECASE)
        return xml

    def midi_fix(self, xml, instrument_data):
        root = etree.fromstring(xml.encode('utf-8'))

        # Remove existing midi tags
        for midi_device in root.findall(".//midi-device"):
            midi_device.getparent().remove(midi_device)
        for midi_instr in root.findall(".//midi-instrument"):
            midi_instr.getparent().remove(midi_instr)

        score_part = root.find(".//score-part")
        if score_part is None:
            return xml

        # Add midi-device
        midi_device = etree.SubElement(score_part, "midi-device")
        midi_device.text = "Dfix SynthTool"

        # Add midi-instrument for P1-I1
        midi_instr = etree.SubElement(score_part, "midi-instrument")
        midi_instr.set("id", "P1-I1")
        etree.SubElement(midi_instr, "midi-channel").text = "10"
        etree.SubElement(midi_instr, "midi-bank").text = "15361"
        etree.SubElement(midi_instr, "midi-program").text = "1"
        etree.SubElement(midi_instr, "volume").text = "100"
        etree.SubElement(midi_instr, "pan").text = "0"

        # Add for each instrument
        for entry in instrument_data.values():
            names = entry["names"]
            midi_unpitched = entry["id"]
            matched_id = None
            for name in names:
                found_id = self.find_instrument_id(root, name)
                if found_id:
                    matched_id = found_id
                    break
            if matched_id:
                midi_instr = etree.SubElement(score_part, "midi-instrument")
                midi_instr.set("id", matched_id)
                etree.SubElement(midi_instr, "midi-channel").text = "10"
                etree.SubElement(midi_instr, "midi-bank").text = "15361"
                etree.SubElement(midi_instr, "midi-program").text = "1"
                etree.SubElement(midi_instr, "midi-unpitched").text = str(midi_unpitched)
                etree.SubElement(midi_instr, "volume").text = "80"
                etree.SubElement(midi_instr, "pan").text = "0"

        return etree.tostring(root, encoding='unicode')

    def beat_unit_changings_fix(self, xml):
        root = etree.fromstring(xml.encode('utf-8'))
        directions = root.findall(".//direction")
        
        for direction in directions:
            direction_type = direction.find("direction-type")
            if direction_type is None:
                continue
            
            metronome = direction_type.find("metronome")
            if metronome is None:
                continue
            
            beat_units = metronome.findall("beat-unit")
            if len(beat_units) != 2:
                continue
            
            # Get beat units
            beat1 = beat_units[0].text
            beat2 = beat_units[1].text
            
            # Check for dots
            beat1_dot = metronome.find("beat-unit-dot") is not None
            if beat1_dot:
                beat1 = f"Dotted {beat1}"
            
            # Find the note before this direction
            prev_note = None
            parent = direction.getparent()
            idx = list(parent).index(direction)
            for i in range(idx - 1, -1, -1):
                if parent[i].tag == "note":
                    prev_note = parent[i]
                    break
            
            if prev_note is None:
                continue
            
            # Create new direction with words
            word_text = f"{beat1.title()} note = {beat2.lower()} note"
            
            # Replace metronome with words
            direction_type.clear()
            words = etree.SubElement(direction_type, "words")
            words.text = word_text
            
            # Move direction before the note
            parent.remove(direction)
            parent.insert(list(parent).index(prev_note), direction)
        
        return etree.tostring(root, encoding='unicode')

    def buzz_roll_fix(self, xml):
        root = etree.fromstring(xml.encode('utf-8'))
        directions = root.findall(".//direction")
        
        for direction in directions:
            direction_type = direction.find("direction-type")
            if direction_type is None:
                continue
            
            words = direction_type.find("words")
            if words is None or words.get("font-family") != "Maestro" or words.text != "z":
                continue
            
            # Remove the words
            direction_type.remove(words)
            
            # Find next note
            next_note = None
            parent = direction.getparent()
            idx = list(parent).index(direction)
            for i in range(idx + 1, len(parent)):
                if parent[i].tag == "note":
                    next_note = parent[i]
                    break
            
            if next_note is not None:
                # Add notations with tremolo
                notations = next_note.find("notations")
                if notations is None:
                    notations = etree.SubElement(next_note, "notations")
                
                ornaments = notations.find("ornaments")
                if ornaments is None:
                    ornaments = etree.SubElement(notations, "ornaments")
                
                tremolo = etree.SubElement(ornaments, "tremolo")
                tremolo.set("type", "unmeasured")
                tremolo.text = "0"
        
        return etree.tostring(root, encoding='unicode')

    def swing_marks_fix(self, xml):
        root = etree.fromstring(xml.encode('utf-8'))
        directions = root.findall(".//direction")
        
        for direction in directions:
            direction_type = direction.find("direction-type")
            if direction_type is None:
                continue
            
            words = direction_type.find("words")
            if words is None or words.get("font-family") != "MaestroTimes":
                continue
            
            equation = words.text
            metronome_xml = None
            
            if "Å’â€š = Å’ â€°" in equation or "♪ = ♪ ‰" in equation:
                metronome_xml = '''<metronome default-y="40" font-family="MaestroTimes" font-size="13.7" font-weight="bold" halign="left">
    <metronome-note>
      <metronome-type>eighth</metronome-type>
      <metronome-beam number="1">begin</metronome-beam>
    </metronome-note>
    <metronome-note>
      <metronome-type>eighth</metronome-type>
      <metronome-beam number="1">end</metronome-beam>
    </metronome-note>
    <metronome-relation>equals</metronome-relation>
    <metronome-note>
      <metronome-type>quarter</metronome-type>
      <metronome-tuplet bracket="yes" type="start">
        <actual-notes>3</actual-notes>
        <normal-notes>2</normal-notes>
      </metronome-tuplet>
    </metronome-note>
    <metronome-note>
      <metronome-type>eighth</metronome-type>
      <metronome-tuplet type="stop">
        <actual-notes>3</actual-notes>
        <normal-notes>2</normal-notes>
      </metronome-tuplet>
    </metronome-note>
  </metronome>'''
            elif "Å’Š = â€°â€°" in equation or "♪ = ‰‰" in equation:
                metronome_xml = '<words>Swing sixteenth notes as triplets</words>'
            
            if metronome_xml:
                # Parse and replace
                direction_type.clear()
                if metronome_xml.startswith('<metronome'):
                    metronome = etree.fromstring(metronome_xml)
                    direction_type.append(metronome)
                else:
                    words_elem = etree.fromstring(metronome_xml)
                    direction_type.append(words_elem)
        
        return etree.tostring(root, encoding='unicode')

    def remove_single_multimeasure_rests(self, xml):
        root = etree.fromstring(xml.encode('utf-8'))
        measures = root.findall(".//measure")
        
        for measure in measures:
            attributes = measure.find("attributes")
            if attributes is None:
                continue
            
            measure_style = attributes.find("measure-style")
            if measure_style is None:
                continue
            
            multiple_rest = measure_style.find("multiple-rest")
            if multiple_rest is None or multiple_rest.text != "1":
                continue
            
            # Remove multiple-rest
            measure_style.remove(multiple_rest)
            
            # Remove forward
            forward = measure.find("forward")
            if forward is not None:
                measure.remove(forward)
            
            # Add note with rest measure="yes"
            rest_note = etree.Element("note")
            rest = etree.SubElement(rest_note, "rest")
            rest.set("measure", "yes")
            measure.append(rest_note)
        
        return etree.tostring(root, encoding='unicode')

    def sticking_to_lyrics(self, xml):
        xml = re.sub(r'>(R|L)(<\s*\/*[^>]*>)', r'>&#8203;\1&#8203;\2', xml)
        return xml

    def remove_prevent_new_systems(self, xml):
        xml = re.sub(r'\s*new-system\s*=\s*(["\'])no\1', '', xml)
        return xml

    def tuplet_based_time_modification(self, xml):
        root = etree.fromstring(xml.encode('utf-8'))
        notes = root.findall(".//note")
        
        for note in notes:
            notations = note.find("notations")
            if notations is None:
                continue
            
            tuplet = notations.find("tuplet")
            if tuplet is None:
                continue
            
            tuplet_actual = tuplet.find("tuplet-actual")
            tuplet_normal = tuplet.find("tuplet-normal")
            if tuplet_actual is None or tuplet_normal is None:
                continue
            
            actual_notes = tuplet_actual.find("tuplet-number")
            normal_notes = tuplet_normal.find("tuplet-number")
            normal_type = tuplet_normal.find("tuplet-type")
            
            # Remove existing time-modification
            time_mod = note.find("time-modification")
            if time_mod is not None:
                note.remove(time_mod)
            
            # Create new time-modification
            time_mod = etree.Element("time-modification")
            
            if actual_notes is not None:
                actual = etree.SubElement(time_mod, "actual-notes")
                actual.text = actual_notes.text
            
            if normal_notes is not None:
                normal = etree.SubElement(time_mod, "normal-notes")
                normal.text = normal_notes.text
            
            if normal_type is not None:
                normal_type_elem = etree.SubElement(time_mod, "normal-type")
                normal_type_elem.text = normal_type.text
            
            # Insert after type
            type_elem = note.find("type")
            if type_elem is not None:
                idx = list(note).index(type_elem)
                note.insert(idx + 1, time_mod)
            else:
                note.append(time_mod)
        
        return etree.tostring(root, encoding='unicode')